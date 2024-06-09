import skimage
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter, map_coordinates
import random
import argparse
import os


def set_seed(seed: int = 42):
    '''set the radom seed'''
    np.random.seed(seed)
    random.seed(seed)
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    print(f"Random seed set as {seed}")
    

def Gaussian_Noise(image_path):
    origin = skimage.io.imread(image_path)
    noisy = skimage.util.random_noise(origin, mode='gaussian',var=0.1)*255
    noisy = noisy[:, :, ::-1]
    
    return noisy

def Shot_Noise(image_path):
    origin = skimage.io.imread(image_path)
    noisy = skimage.util.random_noise(origin, mode='poisson')*255
    noisy = noisy[:, :, ::-1]
    
    return noisy

def Speckle_Noise(image_path):
    origin = skimage.io.imread(image_path)
    noisy = skimage.util.random_noise(origin, mode='speckle',var=0.1)*255
    noisy = noisy[:, :, ::-1]
    
    return noisy

def SP_Noise(image_path):
    origin = skimage.io.imread(image_path)
    noisy = skimage.util.random_noise(origin, mode='s&p',amount=0.1)*255
    noisy = noisy[:, :, ::-1]
    
    return noisy


def motion_blur(image_path, degree=20, angle=45):
    img = cv2.imread(image_path)
    image = np.array(img)

    M = cv2.getRotationMatrix2D((degree / 2, degree / 2), angle, 1)
    motion_blur_kernel = np.diag(np.ones(degree))
    motion_blur_kernel = cv2.warpAffine(motion_blur_kernel, M, (degree, degree))

    motion_blur_kernel = motion_blur_kernel / degree
    blurred = cv2.filter2D(image, -1, motion_blur_kernel)

    # convert to uint8
    cv2.normalize(blurred, blurred, 0, 255, cv2.NORM_MINMAX)
    blurred_image = np.array(blurred, dtype=np.uint8)
    return blurred_image

def guassian_blur(image_path):
    img = cv2.imread(image_path)
    blurred_image = cv2.GaussianBlur(img, ksize=(19, 19), sigmaX=0, sigmaY=0)
    
    return blurred_image

def glass_blur(image_path, kernel_size=3, sigma=3):
    image = cv2.imread(image_path)
    # Generate random noise
    noise = np.random.normal(0, sigma, image.shape).astype(np.uint8)

    # Create a copy of the image with added noise
    noisy_image = cv2.add(image, noise)

    # Apply a median blur to the noisy image
    blurred_image = cv2.medianBlur(noisy_image, kernel_size)

    return blurred_image

def defocus_blur(image_path, kernel_size=2):
    image = cv2.imread(image_path)
    # Create a circular kernel for defocus blur
    kernel = np.zeros((kernel_size, kernel_size), dtype=np.uint8)
    cv2.circle(kernel, (kernel_size // 2, kernel_size // 2), kernel_size // 2, 255, -1)

    # Apply the kernel to the image using filter2D
    blurred_image = cv2.filter2D(image, -1, kernel)

    return blurred_image

def elastic_transform(image_path, alpha=2000, sigma=20, random_state=None):
    image = cv2.imread(image_path)
    if random_state is None:
        random_state = np.random.RandomState(None)

    shape = image.shape
    dx = gaussian_filter((random_state.rand(*shape) * 2 - 1), sigma, mode="constant", cval=0) * alpha
    dy = gaussian_filter((random_state.rand(*shape) * 2 - 1), sigma, mode="constant", cval=0) * alpha

    x, y = np.meshgrid(np.arange(shape[1]), np.arange(shape[0]))
    indices = np.reshape(y+dy, (-1, 1)), np.reshape(x+dx, (-1, 1))

    transformed_image = map_coordinates(image, indices, order=1, mode='reflect')
    transformed_image = transformed_image.reshape(image.shape)

    return transformed_image


def jpeg_compression(image_path, quality=50):
    image = cv2.imread(image_path)
    # Encode the image to JPEG format with specified quality
    _, compressed_image = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

    # Decode the compressed image
    decompressed_image = cv2.imdecode(compressed_image, cv2.IMREAD_COLOR)

    return decompressed_image


def spatter(image_path, spatter_density=0.001):
    image = cv2.imread(image_path)
    # Define spatter parameters
    spatter_radius_range = (1, 5)  # Adjust this range to control the size of spatter

    # Convert image to floating-point representation
    image = image.astype(np.float32) / 255.0

    # Generate spatter
    num_spatter = int(spatter_density * image.shape[0] * image.shape[1])
    for _ in range(num_spatter):
        # Generate random coordinates
        x = np.random.randint(0, image.shape[1])
        y = np.random.randint(0, image.shape[0])

        # Generate random color
        color = np.random.uniform(0, 1, 3)

        # Generate random radius
        radius = np.random.randint(spatter_radius_range[0], spatter_radius_range[1])

        # Apply spatter at the specified coordinates
        cv2.circle(image, (x, y), radius, color, -1)

    spatter_image = image*255
    
    return spatter_image

def saturate_transform(image_path, saturation_factor=3):
    image = cv2.imread(image_path)
    # Convert the image to the HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Scale the saturation channel
    hsv_image[:, :, 1] = hsv_image[:, :, 1] * saturation_factor

    # Convert the image back to the BGR color space
    output_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)

    return output_image

def coarse_dropout(image_path, dropout_prob=0.003, dropout_size=5):
    # Load the image
    image = cv2.imread(image_path)

    # Create a copy of the image
    output_image = np.copy(image)

    # Get image dimensions
    height, width, _ = image.shape

    # Calculate the number of pixels to dropout
    num_pixels = int(dropout_prob * height * width)

    # Randomly select pixel coordinates to dropout
    dropout_coords = np.random.randint(0, high=height, size=(num_pixels, 2))

    # Apply dropout by setting selected pixels to black
    for coord in dropout_coords:
        x, y = coord
        x_end = min(x + dropout_size, width)
        y_end = min(y + dropout_size, height)
        output_image[y:y_end, x:x_end, :] = 0

    return output_image

def rotate_image(image_path):
    # Load the image
    image = cv2.imread(image_path)
    
    angle = random.randint(10, 45)

    height, width = image.shape[:2]

    x0, y0 = width//2, height//2
    MAR1 = cv2.getRotationMatrix2D((x0,y0), angle, 1.0)
    rotated_image = cv2.warpAffine(image, MAR1, (width, height))  

    return rotated_image

def shear_image(image_path):
    # Load the image
    image = cv2.imread(image_path)

    shear_factor = random.randint(10,20)/100

    # Get image dimensions
    height, width, _ = image.shape

    # Define the shear matrix
    shear_matrix = np.array([[1, shear_factor, 0],
                             [shear_factor, 1, 0]], dtype=np.float32)

    # Apply the shear transform
    sheared_image = cv2.warpAffine(image, shear_matrix, (width, height))

    return sheared_image

def piecewise_affine(image_path):
    def generate_grid_points(rows, cols, step):
        points = []
        for y in range(0, rows, step):
            for x in range(0, cols, step):
                points.append([x, y])
        return points

    # Load the image
    image = cv2.imread(image_path)

    # Get image dimensions
    height, width, _ = image.shape
    
    control_points = generate_grid_points(height, width, step=100)

    # Define the target control points (destination points)
    target_points = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32)

    # Calculate the transformation matrices for each triangle
    matrices = []
    for i in range(len(control_points) - 1):
        src_points = np.array([control_points[i], control_points[i + 1], target_points[i]], dtype=np.float32)
        matrix = cv2.getAffineTransform(src_points, target_points[i:i + 2])
        matrices.append(matrix)

    # Apply the piecewise affine transform
    output_image = np.zeros_like(image)
    for matrix in matrices:
        warped_image = cv2.warpAffine(image, matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        output_image = np.maximum(output_image, warped_image)

    return output_image


def corruption(image_path,output_path,state):
    '''corruption scenario'''
    # support corruption functions
    functions = [Gaussian_Noise,Shot_Noise,Speckle_Noise,
                 SP_Noise,motion_blur,guassian_blur,jpeg_compression,
                 spatter,coarse_dropout,rotate_image,shear_image]
    
    # random choice a corruption scenario
    if state == 'random':
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        function = random.choice(functions)
        img = function(image_path)
        output_path = os.path.join(output_path,image_path.split("/")[-1])
        print(output_path)
        cv2.imwrite(output_path,img)
    # individually generate corrupted images for each corruption type
    elif state == 'all':
        for function in functions:
            folder_name = function.__name__
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            img = function(image_path)
            output_path = os.path.join(folder_name,image_path.split("/")[-1])
            cv2.imwrite(output_path,img)       
    else:
        raise TypeError("only support 2 states, i.e., random and all")    

def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dysca Benchmark Generator',
        description='A script for generating corrupted images of Dysca Benchmark')
    parser.add_argument('--input_file', default='./Dysca.json', help="The input json file")  
    parser.add_argument('--input_image_dir', default='./Dysca', help="The input image folder path")  
    parser.add_argument('--output_image_dir', default='./Dysca_corruption', help='The output image folder path')  
    parser.add_argument('--seed', type=int, default=2024)
    
    return parser.parse_args()
    
if __name__ == '__main__': 
    args = parse_args()
    set_seed(args.seed)
    
    if not os.path.exists(args.output_image_dir):
        os.mkdir(args.output_image_dir)
        
    for image in os.listdir(args.input_image_dir):
        image_path = os.path.join(args.input_image_dir,image)
        corruption(image_path,output_path=args.output_image_dir,state='random')