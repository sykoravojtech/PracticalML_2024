import os
import torch

"""
cls weights vector size 157

try: 
    negative/positive
    all 5s 10s more than 2s
    torch.load for .pt
    then concatenate all of them and obtain n x 157 
"""

charades_class_counts_train = [
    635, 640, 479, 303, 266, 81, 618, 27, 784, 879, 46, 728, 202, 42, 241, 1055, 
    673, 219, 298, 217, 678, 356, 280, 278, 89, 187, 615, 280, 248, 92, 257, 58, 
    483, 575, 276, 286, 154, 125, 232, 96, 331, 181, 201, 180, 154, 34, 100, 259, 
    99, 91, 82, 347, 341, 233, 177, 162, 160, 196, 73, 1260, 46, 1075, 495, 683, 
    52, 459, 29, 400, 154, 161, 443, 205, 323, 200, 105, 139, 385, 171, 159, 161, 
    134, 503, 228, 74, 133, 28, 62, 231, 198, 53, 87, 39, 305, 94, 111, 37, 449, 
    1444, 364, 100, 127, 25, 237, 36, 207, 189, 1134, 1014, 276, 481, 536, 49, 
    410, 595, 218, 324, 168, 175, 763, 452, 375, 112, 160, 484, 168, 395, 308, 
    478, 282, 162, 207, 46, 353, 98, 257, 315, 35, 213, 57, 81, 31, 506, 192, 
    250, 165, 237, 245, 338, 332, 588, 357, 964, 1029, 643, 1341, 395, 936
]

def compute_cls_weights(encodings_dir) -> torch.Tensor:
    """
    Calculate class weights for imbalanced dataset.
    """
    print("==> Calculating class weights")

    # Collect all train_y_*.pt files
    train_y_files = [filename for filename in os.listdir(encodings_dir) if filename.startswith("train_y_")]

    # Initialize an empty list to store the tensors
    all_labels = []

    # Load and concatenate all the label files
    for filename in train_y_files:
        file_path = os.path.join(encodings_dir, filename)
        labels = torch.load(file_path)
        all_labels.append(labels)
        # print(file_path)
        # print(labels, labels.shape)

        # Concatenate all the labels into a single tensor
    all_labels = torch.cat(all_labels, dim=0)  # Shape: (n_batches * 16, 157)

    # Calculate the number of positive samples for each class
    positives = torch.sum(all_labels, dim=0)  # Shape: (157,)
    print(f"{positives=}")

    # Calculate the total number of samples
    total_samples = all_labels.size(0)  # Total number of samples (n_batches * 16)

    # Calculate the frequency of each class
    class_freq = positives / total_samples

    # Calculate the class weights as the inverse of the class frequencies
    class_weights = 1.0 / (class_freq + 1e-10)  # Add a small value to avoid division by zero

    # Normalize the class weights by the total number of samples
    class_weights = class_weights * total_samples / torch.sum(class_weights)

    return class_weights


# weights = compute_cls_weights("../../data/encodings/cls_vm_charades")
# weights = compute_cls_weights("../../data/encodings/cls_vm_charades_all_hiddens")
# print(f"{weights=}")

cls_weights = [21.6944,  22.5765,  33.4059,  55.8278,  48.1139, 159.2608,  32.8714,
        477.7824,  24.0288,  19.7165, 192.0060,  14.4987,  58.2001, 281.4335,
         41.8424,  11.5679,  19.1648,  89.3245,  57.2274,  53.7818,  18.5924,
         42.3601,  58.2001,  60.4254, 195.6633, 119.4456,  19.9656,  58.8672,
         70.3584, 159.2608,  66.2730, 331.3652,  24.3998,  22.9549,  59.7228,
         62.4457, 123.0218, 123.0218,  55.5261, 164.3571,  37.2861,  78.1165,
         87.0536,  85.6027,  94.6758, 893.2453, 193.8174,  49.1499, 169.7904,
        203.4123, 207.5216,  38.3296,  37.0174,  48.5689,  83.5148,  70.1182,
         90.5050,  76.9462, 270.3242,   8.6250, 316.0714,  11.7063,  29.7748,
         21.5579, 466.9237,  29.2242, 477.7824,  32.0509, 110.4551,  91.3095,
         26.8207,  67.3595,  36.6215,  82.1786, 193.8174,  92.5434,  32.2522,
         99.7313,  67.1394,  99.2495, 123.0218,  32.4560,  51.1061, 270.3242,
         97.3680, 360.4323, 263.3928,  78.7151,  71.3356, 250.5444, 159.2608,
        570.6845,  50.3545, 117.3980, 124.5130, 336.7974,  27.8383,  15.3777,
         33.7905, 178.6491, 130.8576, 555.2606,  50.7275, 380.4564,  84.8952,
        129.2116,  14.6225,  12.9537,  53.6414,  37.4219,  30.9874, 244.5791,
         43.7120,  26.0388,  53.3627,  37.2186, 104.2875,  98.2997,  18.0374,
         39.7382,  42.0136, 109.2800,  82.1786,  22.9549,  72.5959,  26.1050,
         67.3595,  28.3766,  50.3545,  98.7723,  61.6956, 236.1453,  32.6105,
        132.5461,  47.1207,  38.9103, 211.8004,  59.5497, 270.3242, 209.6392,
        684.8214,  36.4267, 104.8196,  68.7112,  84.5459,  49.7449,  54.4951,
         34.5288,  35.1792,  25.4896,  55.2275,  16.8814,  14.8444,  25.2702,
         13.7606,  34.0707,  14.4376]

cls_weights_all_hidden = [ 23.1028,  23.9438,  35.4918,  56.1243,  47.6168, 152.5118,  31.8406,
        467.7029,  24.9073,  20.0063, 241.9153,  14.7179,  57.6620, 328.8536,
         43.6652,  11.6796,  19.0295,  90.7182,  57.1919,  53.8277,  20.9419,
         47.9422,  62.0844,  57.5044, 204.3362, 103.1697,  19.0467,  53.0142,
         73.8478, 148.2157,  63.5850, 314.1288,  25.6666,  21.8553,  70.6263,
         60.8284, 137.5597, 112.5488,  58.3009, 187.9163,  41.3490,  91.9067,
         88.8043,  92.7164, 115.6408, 725.7458, 223.9003,  48.3831, 194.8762,
        210.4663, 236.4790,  34.1666,  36.0387,  54.1044,  76.5332,  75.9806,
         86.2567,  78.2402, 269.8286,   9.2269, 284.4139,  11.7776,  33.7286,
         23.4372, 447.8006,  28.7916, 526.1657,  30.8150, 120.9576, 110.7717,
         30.8602,  84.8654,  40.8672,  87.3304, 214.7615, 108.4878,  34.9612,
        100.2220,  87.6943, 115.6408, 150.3331,  34.8454,  55.0959, 269.8286,
         93.9582, 467.7029, 280.6217,  82.8607,  69.4608, 288.3100, 219.2357,
        273.3328,  49.7556, 134.0550, 131.5414, 362.8729,  31.0881,  14.4849,
         32.7829, 138.4647, 115.6408, 568.8278,  48.7190, 318.8883,  94.3795,
        132.3687,  14.1063,  12.0129,  46.7703,  33.5137,  27.6565, 181.4364,
         46.2563,  30.2829,  53.4178,  37.4495,  92.3098,  91.9067,  17.1250,
         35.1363,  42.0092, 110.1918,  82.8607,  25.3269,  77.9505,  26.9138,
         67.4571,  25.6042,  54.8089, 109.0499,  70.3901, 382.6660,  35.9157,
        147.1792,  50.8373,  39.0476, 350.7771,  60.3055, 259.8349, 168.3730,
        382.6660,  39.4871, 106.2961,  76.2559,  97.8913,  50.5929,  58.1399,
         43.0401,  35.6722,  29.1101,  54.1044,  17.1950,  16.1648,  24.5872,
         14.6462,  37.9903,  14.2015]