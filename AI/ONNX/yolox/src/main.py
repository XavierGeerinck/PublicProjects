#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Megvii, Inc. and its affiliates.

import argparse
import os

import cv2
import numpy as np
import time

import onnxruntime

from yolox_files.data_augment import preproc as preprocess
from yolox_files.coco_classes import COCO_CLASSES
from yolox_files.utils import mkdir, multiclass_nms, demo_postprocess
from yolox_files.visualize import vis


def make_parser():
    parser = argparse.ArgumentParser("onnxruntime inference sample")
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="yolox.onnx",
        help="Input your onnx model.",
    )
    parser.add_argument(
        "-i",
        "--image_path",
        type=str,
        default='test_image.png',
        help="Path to your input image.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default='demo_output',
        help="Path to your output directory.",
    )
    parser.add_argument(
        "-s",
        "--score_thr",
        type=float,
        default=0.3,
        help="Score threshould to filter the result.",
    )
    parser.add_argument(
        "--input_shape",
        type=str,
        default="640,640",
        help="Specify an input shape for inference.",
    )
    parser.add_argument(
        "--with_p6",
        action="store_true",
        help="Whether your model uses p6 in FPN/PAN.",
    )
    return parser


if __name__ == '__main__':
    args = make_parser().parse_args()

    input_shape = tuple(map(int, args.input_shape.split(',')))
    origin_img = cv2.imread(args.image_path)
    img, ratio = preprocess(origin_img, input_shape)

    session = onnxruntime.InferenceSession(
        path_or_bytes=args.model,
        providers=["CUDAExecutionProvider"]
    )

    ort_inputs = {session.get_inputs()[0].name: img[None, :, :, :]}
    t0 = time.time()
    output = session.run(None, ort_inputs)
    t1 = time.time()
    print(f"Done in: {(t1 - t0) * 1000}ms")
    predictions = demo_postprocess(output[0], input_shape, p6=args.with_p6)[0]

    boxes = predictions[:, :4]
    scores = predictions[:, 4:5] * predictions[:, 5:]

    boxes_xyxy = np.ones_like(boxes)
    boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.
    boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.
    boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2.
    boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2.
    boxes_xyxy /= ratio
    dets = multiclass_nms(boxes_xyxy, scores, nms_thr=0.45, score_thr=0.1)
    if dets is not None:
        final_boxes, final_scores, final_cls_inds = dets[:, : 4], dets[:, 4], dets[:, 5]
        origin_img = vis(origin_img, final_boxes, final_scores, final_cls_inds, conf=args.score_thr, class_names=COCO_CLASSES)

    print("Info")
    print(f"Image Shape: {origin_img.shape[1]}x{origin_img.shape[0]}")
    print(f"Model Shape: {input_shape[0]}x{input_shape[1]}")
    print("Bounding Boxes")
    print(final_boxes)

    mkdir(args.output_dir)
    output_path = os.path.join(args.output_dir, args.image_path.split("/")[-1])
    cv2.imwrite(output_path, origin_img)
