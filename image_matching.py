import torch
import torchvision.transforms as transforms
from torchvision.models import resnet18, ResNet18_Weights
from PIL import Image
from torch.nn.functional import cosine_similarity


# -----------------------------------
# LOAD PRE-TRAINED AI MODEL
# -----------------------------------

weights = ResNet18_Weights.DEFAULT

model = resnet18(weights=weights)

# Remove the final classification layer
model.fc = torch.nn.Identity()

# Evaluation mode
model.eval()


# -----------------------------------
# IMAGE PREPROCESSING
# -----------------------------------

transform = weights.transforms()


# -----------------------------------
# EXTRACT IMAGE FEATURES
# -----------------------------------

def get_image_features(image_path):

    image = Image.open(image_path).convert("RGB")

    image = transform(image)

    image = image.unsqueeze(0)

    with torch.no_grad():

        features = model(image)

    return features


# -----------------------------------
# CALCULATE IMAGE SIMILARITY
# -----------------------------------

def calculate_image_similarity(image1_path, image2_path):

    features1 = get_image_features(image1_path)

    features2 = get_image_features(image2_path)

    similarity = cosine_similarity(
        features1,
        features2
    )

    score = similarity.item()

    # Convert -1 to 1 range into 0 to 100
    score = ((score + 1) / 2) * 100

    return round(score, 2)


# -----------------------------------
# TEST
# -----------------------------------

if __name__ == "__main__":

    image_path = input(
        "Enter image path: "
    )

    score = calculate_image_similarity(
        image_path,
        image_path
    )

    print()
    print("Image Similarity Score:", score, "%")