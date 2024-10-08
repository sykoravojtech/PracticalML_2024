import os
import argparse
from glob import glob
import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from fvcore.common.config import CfgNode
from lightning import Trainer
from lightning.pytorch.loggers import WandbLogger
from lightning.pytorch.callbacks import LearningRateMonitor, ModelCheckpoint
import wandb

from src.datasets import create_dataset, classification_collate_fn, captioning_collate_fn
from src.utils.general import set_deterministic
from src.models.captioning_model import VideoCaptioningModel
from src.models.encoders import EncoderAbstract



parser = argparse.ArgumentParser(description="Train a video model")
parser.add_argument("-c", "--config", help="The config file", 
                        default="src/config/cls_svt_ucf101_s224_f8_exp0.yaml")

args = parser.parse_args()

class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.lin1 = nn.Linear(1569, 1)
        self.lin2 = nn.Linear(768, 768)
        self.norm = nn.LayerNorm(768)
    
    def forward(self, x):
        x = self.lin1(x.permute(0,1,3,2)).flatten(2)
        return self.norm(F.relu(self.lin2(x)))

class VideoCaptioningModelHead(VideoCaptioningModel):
    def __init__(self, config: CfgNode) -> None:
        super().__init__(config)

    def create_encoder(self) -> EncoderAbstract:
        # return nn.Identity()
        # return nn.Sequential(nn.Linear(576, 768))
        # return nn.Sequential(nn.Linear(self.config.DATA.NUM_SAMPLED_FRAMES_MULT*self.config.MODEL.ENCODER.HIDDEN_SIZE, 768))
        return Encoder()

def get_collate_fn(config: CfgNode):
    if config.MODEL.TYPE == 'classification':
        return classification_collate_fn(config)
    elif config.MODEL.TYPE == 'captioning':
        return captioning_collate_fn(config)
    else:
        raise ValueError("Invalid model type")

class CaptioningDataset(Dataset):
    def __init__(self, train: bool):
        super().__init__()
        if train:
            self.x = sorted(glob("data/encodings_svt_8x4_all/train_x_*.pt"))
            self.y = sorted(glob("data/encodings_svt_8x4_all/train_y_*.pt"))
        else:
            self.x = sorted(glob("data/encodings_svt_8x4_all/val_x_*.pt"))
            self.y = sorted(glob("data/encodings_svt_8x4_all/val_y_*.pt"))
        
    def __len__(self):
        return len(self.x)

    def __getitem__(self, ind):
        return torch.load(self.x[ind]), torch.load(self.y[ind])

def train():
    """Train a new model"""

    # Load config
    config = CfgNode.load_yaml_with_base(args.config)
    config = CfgNode(config)

    # make reproducible
    set_deterministic(config.SEED)

    # Wandb init
    # wandb.login(key=config.WANDB_KEY)
    # wandb.init(project=config.PROJECT_NAME,
    #             name=config.EXPERIMENT,
    #             group=config.MODEL.TYPE)

    # create dataset
    # dataset = create_dataset(config)
    train_dataset = CaptioningDataset(True) # dataset.get_train_dataset()
    val_dataset = CaptioningDataset(False) # dataset.get_val_dataset()

    # create dataloaders
    batch_size = config.TRAIN.BATCH_SIZE
    num_workers = config.DATA.NUM_WORKERS
    # collate_fn = get_collate_fn(config)
    train_loader = DataLoader(train_dataset,batch_size=batch_size, shuffle=True,
                                              pin_memory=True,drop_last=False,num_workers=num_workers,
                                               )
    valid_loader = DataLoader(val_dataset,batch_size=batch_size, shuffle=False,
                                num_workers=num_workers,
                                pin_memory=True,drop_last=False,
                                )
    # crete model
    lit_module = VideoCaptioningModelHead(config)

    # callbacks
    output_dir = os.path.join(config.OUTPUT_DIR, config.EXPERIMENT)
    # wandb_logger = WandbLogger(project=config.PROJECT_NAME)
    lr_monitor = LearningRateMonitor(logging_interval='step')
    # checkpoint_monitor_criterion = config.TRAIN.BEST_CHECKPOINT_BY
    checkpointer = ModelCheckpoint(
         dirpath=os.path.join(output_dir,),
        #  filename='{epoch:}-{%s:.3f}'%(checkpoint_monitor_criterion),
        #  monitor=checkpoint_monitor_criterion,
         verbose=True,
         save_weights_only=True,
        #  mode='min' if 'loss' in checkpoint_monitor_criterion else 'max',
         save_last=True,
         every_n_epochs=5,
         save_top_k=-1
    )
    
    # trainer
    trainer = Trainer(default_root_dir=output_dir, precision=config.TRAIN.PRECISION, max_epochs=config.TRAIN.NUM_EPOCHS,
                     check_val_every_n_epoch=1, enable_checkpointing=True,
                     log_every_n_steps=config.TRAIN.LOG_STEPS,
                    #  logger=wandb_logger,
                     callbacks=[lr_monitor, checkpointer],
                     accelerator=config.TRAIN.ACCELERATOR, devices=config.TRAIN.DEVICES)

    # training
    trainer.fit(model=lit_module, train_dataloaders=train_loader, val_dataloaders=valid_loader)
   

if __name__ == '__main__':
    train()
