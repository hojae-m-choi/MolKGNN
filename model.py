from models.GCNNet.GCNNet import GCNNet
from models.KGNN.KGNNNet import KGNNNet
from evaluation import calculate_logAUC, calculate_ppv, calculate_accuracy

# Public libraries
import os
import pytorch_lightning as pl
from torch.nn import Linear, Sigmoid, BCEWithLogitsLoss, Embedding
from torch_geometric.data import Data
import torch



class GNNModel(pl.LightningModule):
    """
    A wrapper for different GNN models

    It uses a GNN model to output a graph embedding, and use some prediction
    method to output a final prediction

    Here a linear layer with a sigmoid function is used
    """

    def __init__(self,
                 gnn_type,
                 num_layers,
                 input_dim,
                 hidden_dim,
                 output_dim,
                 warmup_iterations,
                 tot_iterations,
                 peak_lr,
                 end_lr,
                 loss_func=BCEWithLogitsLoss(),
                 args=None
                 ):
        super(GNNModel, self).__init__()
        print(f'kwargs:{args}')

        if gnn_type == 'gcn':
            self.gnn_model = GCNNet(input_dim, hidden_dim)
        if gnn_type == 'kgnn':
            self.gnn_model = KGNNNet(num_layers=num_layers,
                                     # num_kernel1_1hop=kwargs['num_kernel1_1hop'],
                                     # num_kernel2_1hop=kwargs[
                                     #     'num_kernel2_1hop'],
                                     # num_kernel3_1hop=kwargs[
                                     #     'num_kernel3_1hop'],
                                     # num_kernel4_1hop=kwargs[
                                     #     'num_kernel4_1hop'],
                                     # num_kernel1_Nhop=kwargs[
                                     #     'num_kernel1_Nhop'],
                                     # num_kernel2_Nhop=kwargs[
                                     #     'num_kernel2_Nhop'],
                                     # num_kernel3_Nhop=kwargs[
                                     #     'num_kernel3_Nhop'],
                                     # num_kernel4_Nhop=kwargs[
                                     #     'num_kernel4_Nhop'],
                                     num_kernel1_1hop = args.num_kernel1_1hop,
                                     num_kernel2_1hop = args.num_kernel2_1hop,
                                     num_kernel3_1hop = args.num_kernel3_1hop,
                                     num_kernel4_1hop = args.num_kernel4_1hop,
                                     num_kernel1_Nhop = args.num_kernel1_Nhop,
                                     num_kernel2_Nhop = args.num_kernel2_Nhop,
                                     num_kernel3_Nhop = args.num_kernel3_Nhop,
                                     num_kernel4_Nhop = args.num_kernel4_Nhop,
                                     x_dim = input_dim,
                                     graph_embedding_dim = hidden_dim,
                                     predefined_kernelsets=False
                                     )
        else:
            raise ValueError("model.py::GNNModel: GNN model type is not "
                             "defined.")
        self.atom_encoder = Embedding(118, hidden_dim)
        self.linear = Linear(hidden_dim, hidden_dim)
        self.lin2 = Linear(hidden_dim, output_dim)
        self.activate_func = Sigmoid()  # Not used
        self.warmup_iterations = warmup_iterations
        self.tot_iterations = tot_iterations
        self.peak_lr = peak_lr
        self.end_lr = end_lr
        self.loss_func = loss_func
        self.graph_embedding = None
        self.smiles_list = None

    def forward(self, data):
        # print(f'model.py::x before:{data.x.shape}')
        # print(f'model.py::atomic_num:{data.atomic_num}')
        data.x = self.atom_encoder(data.atomic_num)
        # print(f'model.py::data.x.shape:{data.x.shape}')
        # print(f'model.py::data.x:{data.x}')
        graph_embedding = self.gnn_model(data)
        prediction = self.lin2(self.activate_func(self.linear(
            graph_embedding)))

        # # Debug
        # print(f'model.py::smiles:{data.smiles}\n ')
        # print(f'prediction:\n{prediction}\n ')
        # print(f'graph_embedding:\n:{graph_embedding}')
        self.graph_embedding = graph_embedding
        self.smiles_list = data.smiles
        return prediction, graph_embedding

    def save_atom_encoder(self, dir, file_name):
        if not os.path.exists(dir):
            os.mkdir(dir)
        torch.save(self.atom_encoder.state_dict(), dir+file_name)



    def save_graph_embedding(self, dir):
        if not os.path.exists(dir):
            os.mkdir(dir)
        torch.save(self.graph_embedding, f'{dir}/graph_embedding.pt')
        with open(f'{dir}/smiles_for_graph_embedding.txt', 'w+') as f:
            for smiles in self.smiles_list:
                f.write(smiles+ "\n")

    def save_kernels(self, dir, file_name):
        """
        Save the kernels. Unique for Kernel GNN
        :param file_name:
        :return:
        """
        if isinstance(self.gnn_model, KGNNNet):
            if not os.path.exists(dir):
                os.mkdir(dir)
            torch.save(self.gnn_model.gnn.layers[
                           0].trainable_kernelconv_set.state_dict(),
                       dir+file_name)
        else:
            raise Exception("model.py::GNNModel.sve_kernels(): only "
                            "implemented for Kernel GNN")
    def print_graph_embedding(self):
        print(self.graph_embedding)


    @staticmethod
    def add_model_args(gnn_type, parent_parser):
        """
        Add model arguments to the parent parser
        :param gnn_type: a lowercase string specifying GNN type
        :param parent_parser: parent parser for adding arguments
        :return: parent parser with added arguments
        """
        parser = parent_parser.add_argument_group("GNN_Model")

        # Add general model arguments below
        # E.g., parser.add_argument('--general_model_args', type=int,
        # default=12)
        parser.add_argument('--seed', type=int, default=42)
        parser.add_argument('--input_dim', type=int, default=32)
        parser.add_argument('--hidden_dim', type=int, default=32)
        parser.add_argument('--output_dim', type=int, default=32)
        parser.add_argument('--validate', action='store_true', default=False)
        parser.add_argument('--test', action='store_true', default=False)
        parser.add_argument('--warmup_iterations', type=int, default=60000)
        parser.add_argument('--tot_iterations', type=int, default=1000000)
        parser.add_argument('--peak_lr', type=float, default=2e-4)
        parser.add_argument('--end_lr', type=float, default=1e-9)

        if gnn_type == 'gcn':
            GCNNet.add_model_specific_args(parent_parser)
        elif gnn_type == 'kgnn':
            KGNNNet.add_model_specific_args(parent_parser)
        return parent_parser

    def training_step(self, batch_data, batch_idx):
        """
        Training operations for each iteration includes getting the loss and
        metrics.
        The backpropagation is NOT explicitly specified in this function but
        will be taken care of by the pytorch lightning library, as long as
        there is a "loss" key in the output dictionary
        :param batch_data: the data from each mini-batch
        :param batch_idx: the mini-batch id
        :return: a list of dictionaries. Each dicitonary is the output from
        each iteration, and consists of loss, logAUC and ppv
        """

        # Get prediction and ground truth
        pred_y, _ = self(batch_data)
        pred_y = pred_y.view(-1)
        true_y = batch_data.y.view(-1)
        # print(f"models.py::true_y:{true_y}")
        # Get metrics
        results = {}
        loss = self.loss_func(pred_y, true_y.float())
        results['loss'] = loss
        numpy_prediction = pred_y.detach().cpu().numpy()
        numpy_y = true_y.cpu().numpy()
        # logAUC = calculate_logAUC(numpy_y, numpy_prediction)
        # results['logAUC'] = logAUC
        # ppv = calculate_ppv(numpy_y, numpy_prediction)
        # results['ppv'] = ppv
        accuracy = calculate_accuracy(numpy_y, numpy_prediction)
        results['accuracy'] = accuracy

        return results

    def training_epoch_end(self, train_step_outputs):
        """
        Get the mean of loss, logAUC, ppv from all iterations in an epoch
        :param train_step_outputs:
        :return: None, But set self.train_epoch_outputs to a dictionary of
        the mean metrics, for monitoring purposes.
        """
        train_epoch_outputs = {}
        for key in train_step_outputs[0].keys():  # Here train_step_outputs
            # is a list of dictionaries, with each dictionary being the
            # output from each iteration. So train_step_outputs[0] is to get
            # the first dictionary. See return function description from
            # function training_step() above
            mean_output = sum(output[key] for output in train_step_outputs) \
                          / len(train_step_outputs)
            train_epoch_outputs[key] = mean_output

        self.train_epoch_outputs = train_epoch_outputs

    def validation_step(self, batch_data, batch_idx, dataloader_idx):
        """
        Process the data in validation dataloader in evaluation mode
        :param batch_data:
        :param batch_idx:
        :param dataloader_idx:
        :return: It returns a list of lists. The 0th item in the list is the
        outputs (a list) from the validation datasets while the 1st item is the
        outputs from the training datasets. Each output is another list,
        which each item being the dictionary from each step.
        """

        output = self(batch_data)
        pred_y = output[0].view(-1)
        true_y = batch_data.y.view(-1)
        # print(f'y_pred.shape:{y_pred.shape} y_true:{y_true.shape}')

        # Get metrics
        results = {}
        loss = self.loss_func(pred_y, true_y.float())
        results['loss'] = loss
        numpy_prediction = pred_y.detach().cpu().numpy()
        numpy_y = true_y.cpu().numpy()
        # logAUC = calculate_logAUC(numpy_y, numpy_prediction)
        # results['logAUC'] = logAUC
        # ppv = calculate_ppv(numpy_y, numpy_prediction)
        # results['ppv'] = ppv
        accuracy = calculate_accuracy(numpy_y, numpy_prediction)
        results['accuracy'] = accuracy
        return results
        # return {
        #     'loss': loss,
        #     'logAUC': logAUC,
        #     'ppv': ppv,
        #     'accuracy':accuracy
        # }

    def validation_epoch_end(self, valid_step_outputs):
        """
        Evaluate on both the validation and training datasets. Besides in the
        training loop, the training dataset is included again because the
        model is set to evaluation mode (see
        https://stackoverflow.com/questions/60018578/what-does-model-eval-do
        -in-pytorch for a introduction of evaluation mode).
        :param valid_step_outputs: a list of outputs from two dataloader.
        See the return description from function validation_step() above.
        set dataloader
        :return: None. However, set self.valid_epoch_outputs to be a
        dictionary of mean metrics from each validation step, with metrics
        from training dataset with "_no_dropout" suffix, such as
        "loss_no_dropout". The self.valid_epoch_outputs is used for monitoring.
        """
        self.valid_epoch_outputs = {}

        # There are outputs from both validation and training datasets
        # resulting from each validation iteration. Here we get the mean and
        # then store them in self.valid_epoch_outputs
        for i, outputs_each_dataloader in enumerate(valid_step_outputs):
            for key in outputs_each_dataloader[0].keys():
                mean_output = sum(output[key] for output in
                                  outputs_each_dataloader) \
                              / len(outputs_each_dataloader)

                if i ==0:
                    # For validation dataloader, output keys are "loss",
                    # "logAUC", "ppv"
                    pass
                else:
                    # For training dataloader, output keys are "loss_no_dropout",
                    # "logAUC_no_dropout", "ppv_no_dropout"
                    key = key + "_no_dropout"
                self.valid_epoch_outputs[key] = mean_output


    def configure_optimizers(self):
        """
        A required function for pytorch lightning class LightningModule.
        :return: A union of lists, the first one is optimizers and the
        second one is schedulers
        """
        optimizer, scheduler = self.gnn_model.configure_optimizers(
            self.warmup_iterations, self.tot_iterations, self.peak_lr,
            self.end_lr)
        return [optimizer], [scheduler]
