#!/usr/bin/python3
import argparse
import json
import os
import os.path as osp

import cv2
import numpy as np

from coco_utils import create_coco, insert_img_anns

POINTS_WH = 30


def labelme2coco(path, img_root='images'):
    if not img_root:
        img_root = path
    coco = create_coco()
    categories = []
    if osp.isfile(path):
        files = [path]
        path = osp.dirname(path)
    else:
        files = [
            osp.join(path, f) for f in os.listdir(path)
            if osp.splitext(f)[-1] == '.json'
        ]
    for data in files:
        with open(data, 'r') as f:
            data = json.loads(f.read())
        img_info = {
            'file_name':
            osp.relpath(osp.abspath(osp.join(img_root, data['imagePath'])),
                        './'),
            'width':
            data['imageWidth'],
            'height':
            data['imageHeight'],
        }
        anns = []
        for shapes in data['shapes']:
            label = shapes['label']
            if label not in categories:
                coco['categories'][len(categories)]['name'] = label
                categories.append(label)
            cid = categories.index(label)

            points = np.float32(shapes['points']).reshape(-1).tolist()
            # polygon
            if shapes['shape_type'] == 'polygon':
                xs = points[::2]
                ys = points[1::2]
                x1 = min(xs)
                y1 = min(ys)
                w = max(xs) - x1
                h = max(ys) - y1
                anns.append({
                    'area': w * h,
                    'bbox': [x1, y1, w, h],
                    'category_id': cid,
                    'iscrowd': 0,
                    'segmentation': [points]
                })
            elif shapes['shape_type'] == 'line':
                x, y = points[::2], points[1::2]
                x1 = min(x) - POINTS_WH
                y1 = min(y) - POINTS_WH
                x2 = max(x) + POINTS_WH
                y2 = max(y) + POINTS_WH
                w = x2 - x1
                h = y2 - y1
                kps = []
                for x_, y_ in zip(x, y):
                    kps.append(x_)
                    kps.append(y_)
                    kps.append(2)
                anns.append({
                    'area': w * h,
                    'bbox': [x1, y1, w, h],
                    'category_id': cid,
                    'iscrowd': 0,
                    'segmentation': [[x1, y1, x1, y2, x2, y2, x2, y1]],
                    "keypoints": kps,
                    "num_keypoints": len(x)
                })
        coco = insert_img_anns(coco, img_info, anns)
    coco['categories'] = [
        c for c in coco['categories'] if c['name'] is not None
    ]
    save_path = osp.join(path, '../coco.json')
    with open(save_path, 'w') as f:
        f.write(json.dumps(coco, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str)
    parser.add_argument('--img-root', default='images', type=str)
    opt = parser.parse_args()
    labelme2coco(opt.path, opt.img_root)
