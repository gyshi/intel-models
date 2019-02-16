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

import argparse
import os

from common.base_model_init import BaseModelInitializer
from common.base_model_init import set_env_var


class ModelInitializer(BaseModelInitializer):
    def __init__(self, args, custom_args, platform_util):
        self.args = args
        self.custom_args = custom_args
        self.command = ""
        command_prefix = "python generate.py"

        # Set default KMP env vars, except for KMP_SETTINGS
        self.set_kmp_vars(kmp_settings=None)

        self.parse_custom_args()
        num_inter_threads = 1
        num_intra_threads = int(self.args.num_cores)
        set_env_var("OMP_NUM_THREADS", self.args.num_cores)

        if self.args.socket_id != -1:
            command_prefix = "numactl --physcpubind=0-{} --membind={} {}".\
                format(str(int(self.args.num_cores) - 1), self.args.socket_id,
                       command_prefix)
        else:
            command_prefix = "numactl --physcpubind=0-{} -l {}".format(
                str(int(self.args.num_cores) - 1), command_prefix)

        checkpoint_path = os.path.join(self.args.checkpoint,
                                       self.args.checkpoint_name)

        # create command to run benchmarking
        self.command = ("{} {} --num_inter_threads={} "
                        "--num_intra_threads={} --sample={}").format(
            command_prefix, checkpoint_path, str(num_inter_threads),
            str(num_intra_threads), str(self.args.sample))

    def parse_custom_args(self):
        if self.custom_args:
            parser = argparse.ArgumentParser()
            parser.add_argument("--sample", default=None, dest='sample',
                                type=int)
            parser.add_argument("--checkpoint_name", default=None,
                                dest='checkpoint_name', type=str)
            self.args = parser.parse_args(self.custom_args,
                                          namespace=self.args)

    def run(self):
        if self.command:
            # The generate.py script expects that we run from the model source
            # directory.  Save off the current working directory so that we can
            # restore it when the script is done.
            original_dir = os.getcwd()
            os.chdir(self.args.model_source_dir)

            # Run benchmarking
            self.run_command(self.command)

            # Change context back to the original dir
            os.chdir(original_dir)
