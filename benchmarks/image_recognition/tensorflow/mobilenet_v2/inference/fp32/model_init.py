#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: EPL-2.0
#

import os
from common.base_model_init import BaseModelInitializer
from common.base_model_init import set_env_var


class ModelInitializer(BaseModelInitializer):
    """ Model initializer for MobileNet V2 FP32 inference """

    def __init__(self, args, custom_args=[], platform_util=None):
        super(ModelInitializer, self).__init__(args, custom_args, platform_util)

        # use default batch size if -1
        if self.args.batch_size == -1:
            self.args.batch_size = 128

        # Set KMP env vars, if they haven't already been set
        config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
        self.set_kmp_vars(config_file_path)

        # set num_inter_threads and num_intra_threads (override inter threads to 2)
        self.set_num_inter_intra_threads(num_inter_threads=2)

        script_name = "accuracy.py" if self.args.accuracy_only \
            else "eval_image_classifier.py"
        script_path = os.path.join(
            self.args.intelai_models, self.args.mode, self.args.precision,
            script_name)
        self.command_prefix = "{} {}".format(self.python_exe, script_path)

        if self.args.socket_id != -1:
            self.command_prefix = "numactl --cpunodebind={} -l {}".format(
                str(self.args.socket_id), self.command_prefix)

        set_env_var("OMP_NUM_THREADS", self.args.num_intra_threads)

        if not self.args.accuracy_only:
            self.command_prefix = ("{prefix} "
                                   "--dataset_name imagenet "
                                   "--checkpoint_path {checkpoint} "
                                   "--dataset_split_name=validation "
                                   "--clone_on_cpu=True "
                                   "--model_name {model} "
                                   "--inter_op_parallelism_threads {inter} "
                                   "--intra_op_parallelism_threads {intra} "
                                   "--batch_size {bz}").format(
                prefix=self.command_prefix, checkpoint=self.args.checkpoint,
                model=self.args.model_name, inter=self.args.num_inter_threads,
                intra=self.args.num_intra_threads, bz=self.args.batch_size)

            if self.args.data_location:
                self.command_prefix += " --dataset_dir {}".format(self.args.data_location)
        else:
            # add args for the accuracy script
            script_args_list = [
                "input_graph", "data_location", "input_height", "input_width",
                "batch_size", "input_layer", "output_layer",
                "num_inter_threads", "num_intra_threads"]
            self.command_prefix = self.add_args_to_command(
                self.command_prefix, script_args_list)

    def run(self):
        self.run_command(self.command_prefix)
