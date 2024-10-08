
import argparse
import glob
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from fvcore.common.config import CfgNode
from tqdm.auto import tqdm

from src.models.captioning_model import VideoCaptioningModel
from src.datasets import create_dataset, captioning_collate_fn
from src.utils.general import set_deterministic
from torchmetrics.functional.text import bleu_score, rouge_score

parser = argparse.ArgumentParser(description="Train a video model")
parser.add_argument("--config", help="The config file", 
                        default="src/config/cap_svt_charades_s224_f8_exp0.yaml")
parser.add_argument("--weight", help="The path to the trained weight .ckpt file", 
                        default="checkpoints/cap_svt_charades_s224_f8_exp_32_train_all/epoch=11-step=23952.ckpt")

args = parser.parse_args()

class VideoCaptioningModelHead(VideoCaptioningModel):
    def __init__(self, config: CfgNode) -> None:
        super().__init__(config)

    def create_encoder(self):
        return nn.Identity()


# Load config
config = CfgNode.load_yaml_with_base(args.config)
config = CfgNode(config)

# make reproducible
set_deterministic(config.SEED)
# lit_module = create_model(config)

# WEIGHT = sorted(glob.glob('runs/cap_svt_charades_s224_f8_exp0/epoch=*.ckpt'))[-1]
WEIGHT = args.weight
# print(WEIGHT)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
lit_module = VideoCaptioningModelHead.load_from_checkpoint(WEIGHT, map_location=device)
lit_module = lit_module.to("cuda").eval()
tokenizer = lit_module.head.tokenizer

class CaptioningDataset(Dataset):
    def __init__(self, train: bool):
        super().__init__()
        if train:
            self.x = sorted(glob.glob("data/encodings/train_x_*.pt"))
            self.y = sorted(glob.glob("data/encodings/train_y_*.pt"))
        else:
            self.x = sorted(glob.glob("data/encodings/val_x_*.pt"))
            self.y = sorted(glob.glob("data/encodings/val_y_*.pt"))
        
    def __len__(self):
        return len(self.x)

    def __getitem__(self, ind):
        return torch.load(self.x[ind]).squeeze(), torch.load(self.y[ind])

val_dataset = CaptioningDataset(False)

batch_size = 1
num_workers = 16
collate_fn = captioning_collate_fn(config)
val_loader = DataLoader(val_dataset,batch_size=batch_size,num_workers=num_workers,
                                             pin_memory=True,drop_last=False,
                                             prefetch_factor=4)

true_cap = []
pred_cap = []
for i, (X, y) in tqdm(enumerate(val_loader), total=len(val_loader)):
     X = X.to(device)
     for k,v in y.items():
          y[k] = v.to(device)

     generated_cap = lit_module.generate(X, max_len=128, beam_size=3)
     # print('True cap:', tokenizer.decode(y['input_ids'][0].cpu(), skip_special_tokens=True))
     # print("Generated cap:", generated_cap)
     true_cap.append(tokenizer.decode(y['input_ids'][0].cpu().squeeze(), skip_special_tokens=True))
     pred_cap.append(generated_cap)

print("BLEU_1:", bleu_score(pred_cap, true_cap, 1))
print("BLEU_2:", bleu_score(pred_cap, true_cap, 2))
print("BLEU_3:", bleu_score(pred_cap, true_cap, 3))
print("BLEU_4:", bleu_score(pred_cap, true_cap, 4))
print("ROUGE:", rouge_score(pred_cap, true_cap))