"""
Add the Training (TorchSupport-Training API) and loss functions here.
"""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, TensorDataset
from torchsupport.training.vae import VAETraining

# Ignore warnings
import warnings

warnings.filterwarnings("ignore")


class VAEDataset(Dataset):
    def __init__(self, data):
        super(VAEDataset, self).__init__()
        self.data = data

    def __getitem__(self, index):
        data, label = self.data[index]
        return (data,)

    def __len__(self):
        return len(self.data)
        pass


def normalize(image):
    return (image - image.min()) / (image.max() - image.min())

class Encoder(nn.Module):
    def __init__(self, z=32):
        super(Encoder, self).__init__()
        self.z = z
        self.encoder = nn.Sequential(nn.Linear(256 * 320, 128*160), nn.ReLU(),
                                     nn.Linear(128*160, 32*40), nn.ReLU(),
                                     nn.Linear(32*40, 16*20), nn.ReLU(),
                                     nn.Linear(16*20, 128), nn.ReLU(),
                                     nn.Linear(128, z), nn.ReLU())
        self.mean = nn.Linear(z, z)
        self.logvar = nn.Linear(z, z)

    def forward(self, inputs):
        inputs = inputs.view(inputs.size(0), -1)
        features = self.encoder(inputs)
        mean = self.mean(features)
        logvar = self.logvar(features)
        return features, mean, logvar

class Decoder(nn.Module):
  def __init__(self, z=32):
    super(Decoder, self).__init__()
    self.z = z  
    self.decoder = nn.Sequential(
      nn.Linear(z, 128),
      nn.ReLU(),
      nn.Linear(128, 256),
      nn.ReLU(),
      nn.Linear(256, 28 * 32),
      nn.ReLU(),
      nn.Linear(28*32, 36*48),
      nn.ReLU(),
      nn.Linear(36*48, 72*96),
      nn.ReLU(),
      nn.Linear(72*96, 156*212),
      nn.ReLU(),
      nn.Linear(156*212, 256*320)
    )

  def forward(self, sample):
    return self.decoder(sample).view(-1, 1, 256, 320)


class OdirVAETraining(VAETraining):
    def run_networks(self, data, *args):
        mean, logvar, reconstructions, data = super().run_networks(data, *args)
        if self.step_id % 4 == 0:
            self.writer.add_image("target", data[0], self.step_id)
            self.writer.add_image("reconstruction", reconstructions[0], self.step_id)
        return mean, logvar, reconstructions, data


