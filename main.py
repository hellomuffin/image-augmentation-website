# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


import os
from flask import Flask,render_template,request, redirect, url_for
from werkzeug.utils import secure_filename
import numpy as np
import matplotlib.pyplot as plt
import cv2
from batchgenerators.dataloading.data_loader import DataLoaderBase
from batchgenerators.transforms.color_transforms import ContrastAugmentationTransform
from batchgenerators.transforms.spatial_transforms import MirrorTransform
from batchgenerators.transforms.abstract_transforms import Compose
from batchgenerators.dataloading.multi_threaded_augmenter import MultiThreadedAugmenter
from batchgenerators.transforms.spatial_transforms import SpatialTransform


count = 0

UPLOAD_FOLDER = './'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class DataLoader(DataLoaderBase):
    def __init__(self, data, BATCH_SIZE=2, num_batches=None, seed=False):
        super(DataLoader, self).__init__(data, BATCH_SIZE, num_batches, seed)
        # data is now stored in self._data.

    def generate_train_batch(self):
        # usually you would now select random instances of your data. We only have one therefore we skip this
        img = self._data

        # The camera image has only one channel. Our batch layout must be (b, c, x, y). Let's fix that
        img = np.tile(img[None, None], (self.BATCH_SIZE, 1, 1, 1))

        # now construct the dictionary and return it. np.float32 cast because most networks take float
        return {'data': img.astype(np.float32), 'some_other_key': 'some other value'}



def plot_batch(batch):
    global  count
    batch_size = batch['data'].shape[0]
    plt.figure(figsize=(16, 10))
    for i in range(batch_size):
        plt.subplot(1, batch_size, i+1)
        plt.imshow(batch['data'][i, 0], cmap="gray") # only grayscale image here
        filename = "transformed picture"
        filename += str(count)
        filename += ".png"
        if count == 7 or count == 11:
            plt.savefig(filename)
        count += 1
    plt.show()



def main(filename):
    img = cv2.imread(filename)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    batchgen = DataLoader(img, 4, None, False)
    batch = next(batchgen)
    plot_batch(batch)
    my_transforms = []
    brightness_transform = ContrastAugmentationTransform((0.3, 3.), preserve_range=True)
    my_transforms.append(brightness_transform)
    mirror_transform = MirrorTransform(axes=(0, 1))
    my_transforms.append(mirror_transform)

    all_transforms = Compose(my_transforms)
    multithreaded_generator = MultiThreadedAugmenter(batchgen, all_transforms, 4, 2, seeds=None)

    plot_batch(multithreaded_generator.next())
    multithreaded_generator._finish()  # kill the workers

    spatial_transform = SpatialTransform(img.shape, np.array(img.shape) // 2,
                                         do_elastic_deform=True, alpha=(0., 1500.), sigma=(30., 50.),
                                         do_rotation=True, angle_z=(0, 2 * np.pi),
                                         do_scale=True, scale=(0.7, 5),
                                         border_mode_data='constant', border_cval_data=0, order_data=1,
                                         random_crop=False)

    my_transforms.append(spatial_transform)
    all_transforms = Compose(my_transforms)
    multithreaded_generator = MultiThreadedAugmenter(batchgen, all_transforms, 4, 2, seeds=None)
    plot_batch(next(multithreaded_generator))




@app.route("/",methods = ["POST","GET"])
def home():
    if request.method == 'POST' and request.files:
        name = request.form.get('image')
        file = request.files['image']
        filename = secure_filename(file.filename)
        print(filename)
        print(type(filename))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        main(filename)
        return render_template("login.html",content = filename)
    return render_template("index.html")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
