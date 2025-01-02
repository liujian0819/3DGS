#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import torch
import sys
import cv2
from scene import Scene
import os
from tqdm import tqdm
from os import makedirs
from gaussian_renderer import render
import torchvision
from utils.general_utils import safe_state
from argparse import ArgumentParser, Namespace
from arguments import ModelParams, PipelineParams, OptimizationParams
from gaussian_renderer import GaussianModel

def render_set(model_path, name, iteration, views, gaussians, pipeline, background,sty_id:int):
    render_path = os.path.join(model_path, name, "{}".format(sty_id), "renders")
    gts_path = os.path.join(model_path, name, "{}".format(sty_id), "gt")
    videoName=render_path+"\\animation.mp4"
    vid = []
    makedirs(render_path, exist_ok=True)
    makedirs(gts_path, exist_ok=True)
    for idx, view in enumerate(tqdm(views, desc="Rendering progress")):
        rendering = render(view, gaussians, pipeline, background)["render"]
        gt = view.original_image[0:3, :, :]
        torchvision.utils.save_image(rendering, os.path.join(render_path, '{0:05d}'.format(idx) + ".png"))
        torchvision.utils.save_image(gt, os.path.join(gts_path, '{0:05d}'.format(idx) + ".png"))
    files = os.listdir(render_path)
    h, w, _ = cv2.imread(render_path+"\\"+ files[0]).shape
    fps = 15
    vid = cv2.VideoWriter(videoName, cv2.VideoWriter_fourcc(*'xvid'), fps, (w, h))
    for file in files:
        img = cv2.imread(render_path+"\\"+ file)  
        vid.write(img)
	    

def render_sets(dataset : ModelParams, iteration : int, pipeline : PipelineParams, skip_train : bool, skip_test : bool, sty_id:int):
    with torch.no_grad():
        gaussians = GaussianModel(dataset.sh_degree)
        scene = Scene(dataset, gaussians, load_iteration=iteration, shuffle=False,idx=sty_id)

        bg_color = [1,1,1] if dataset.white_background else [0, 0, 0]
        background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

        if not skip_train:
             render_set(dataset.model_path, "train", scene.loaded_iter, scene.getTrainCameras(), gaussians, pipeline, background,sty_id=sty_id)

        if not skip_test:
             render_set(dataset.model_path, "test", scene.loaded_iter, scene.getTestCameras(), gaussians, pipeline, background,sty_id=sty_id)

if __name__ == "__main__":
    # Set up command line argument parser
    parser = ArgumentParser(description="Testing script parameters")
    model = ModelParams(parser)
    op = OptimizationParams(parser)
    pipeline = PipelineParams(parser)
    parser.add_argument("--iteration", default=20000, type=int)
    parser.add_argument("--sty_id", default=0, type=int)
    parser.add_argument("--skip_train", action="store_true")
    parser.add_argument("--skip_test", action="store_false")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(sys.argv[1:])

    print("Rendering " + args.model_path)

    # Initialize system state (RNG)
    safe_state(args.quiet)
    for idx in [0,1,2,3,4]:
       render_sets(model.extract(args), args.iteration, pipeline.extract(args), args.skip_train, args.skip_test, sty_id=idx)