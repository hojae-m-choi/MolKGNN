from ..ChIRoNet.gnn_3D.dimenet_pp import DimeNetPlusPlus

import json


import torch
from torch.nn import ModuleList
from torch.optim import Adam
from torch_geometric.nn.acts import swish
import pytorch_lightning as pl
# from lr import PolynomialDecayLR
# import pytorch_warmup as warmup



class DimeNetPP(torch.nn.Module):
    """
        codes adapted from https://github.com/keiradams/ChIRo
        DimeNet++ implementation based on https://github.com/klicperajo/dimenet.
    Args:
        hidden_channels (int): Hidden embedding size.
        out_channels (int): Size of each output sample.
        num_blocks (int): Number of building blocks.
        int_emb_size (int): Embedding size used for interaction triplets
        basis_emb_size (int): Embedding size used in the basis transformation
        out_emb_channels(int): Embedding size used for atoms in the output block
        num_spherical (int): Number of spherical harmonics.
        num_radial (int): Number of radial basis functions.
        cutoff: (float, optional): Cutoff distance for interatomic
            interactions. (default: :obj:`5.0`)
        envelope_exponent (int, optional): Shape of the smooth cutoff.
            (default: :obj:`5`)
        num_before_skip: (int, optional): Number of residual layers in the
            interaction blocks before the skip connection. (default: :obj:`1`)
        num_after_skip: (int, optional): Number of residual layers in the
            interaction blocks after the skip connection. (default: :obj:`2`)
        num_output_layers: (int, optional): Number of linear layers for the
            output blocks. (default: :obj:`3`)
        act: (function, optional): The activation funtion.
            (default: :obj:`swish`)
    """
    def __init__(self,
            hidden_channels,
            out_channels,
            num_blocks,
            int_emb_size,
            basis_emb_size,
            out_emb_channels,
            num_spherical,
            num_radial,
            cutoff=5.0,
            envelope_exponent=5,
            num_before_skip=1,
            num_after_skip=2,
            num_output_layers=3,
            act=swish,
            MLP_hidden_sizes = [],):
        super(DimeNetPP, self).__init__()
        self.encoder = DimeNetPlusPlus(
            hidden_channels=hidden_channels,  # 128
            out_channels=out_channels,  # 1
            num_blocks=num_blocks,  # 4
            int_emb_size=int_emb_size,  # 64
            basis_emb_size=basis_emb_size,  # 8
            out_emb_channels=out_emb_channels,  # 256
            num_spherical=num_spherical,  # 7
            num_radial=num_radial,  # 6
            cutoff=cutoff,  # 5.0
            envelope_exponent=envelope_exponent,  # 5
            num_before_skip=num_before_skip,  # 1
            num_after_skip=num_after_skip,  # 2
            num_output_layers=num_output_layers,  # 3
            act=act,
            MLP_hidden_sizes=MLP_hidden_sizes,  # [] for contrastive
        )


    def forward(self, batch_data):
        graph_embedding = self.encoder()

        return graph_embedding


    @staticmethod
    def add_model_specific_args(parent_parser):
        """
        Add model arguments to the parent parser
        :param parent_parser: parent parser for adding arguments
        :return: parent parser with added arguments
        """
        parser = parent_parser.add_argument_group("DimeNetPP")

        # Add specific model arguments below
        # E.g., parser.add_argument('--GCN_arguments', type=int,
        # default=12)
        parser.add_argument('--num_blocks', type=int, default=4,
                            help='')
        parser.add_argument('--int_emb_size', type=int, default=64,
                            help='')
        parser.add_argument('--basis_emb_size', type=int, default=8,
                            help='')
        parser.add_argument('--basis_emb_size', type=int, default=8,
                            help='')
        parser.add_argument('--out_emb_channels', type=int, default=256,
                            help='')
        parser.add_argument('--num_spherical', type=int, default=7,
                            help='')
        parser.add_argument('--num_radial', type=int, default=6,
                            help='')
        parser.add_argument('--cutoff', type=float, default=5.0,
                            help='')
        parser.add_argument('--envelop_exponent', type=int, default=5,
                            help='')
        parser.add_argument('--num_before_skip', type=int, default=1,
                            help='')
        parser.add_argument('--num_after_skip', type=int, default=2,
                            help='')
        parser.add_argument('--num_output_layers', type=int, default=3,
                            help='')

        return parent_parser


    # def configure_optimizers(self, warmup_iterations, tot_iterations,
    #                          peak_lr, end_lr):
    #     """
    #     Returns an optimizer and scheduler suitable for GCNNet
    #     :return: optimizer, scheduler
    #     """
    #     optimizer = Adam(self.parameters())
    #     # scheduler = warmup.
    #     scheduler = {
    #         'scheduler': PolynomialDecayLR(
    #             optimizer,
    #             warmup_iterations=warmup_iterations,
    #             tot_iterations=tot_iterations,
    #             lr=peak_lr,
    #             end_lr=end_lr,
    #             power=1.0,
    #         ),
    #         'name': 'learning_rate',
    #         'interval': 'step',
    #         'frequency': 1,
    #     }
    #     return optimizer, scheduler

