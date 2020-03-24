import numpy as np
import PIL as pil
from skimage import io, img_as_ubyte, transform
import pandas as pd


def trim_image_rgb(jpg, dir, outdir):
    """Trims the black margins out of the image
    The original and returned images are rgb"""

    img = io.imread(dir + jpg)
    ts = (img != 0).sum(axis=1) != 0
    ts = ts.sum(axis=1) != 0
    img = img[ts]
    ts = (img != 0).sum(axis=0) != 0
    ts = ts.sum(axis=1) != 0
    img = img[:, ts, :]
    io.imsave(outdir + jpg, img)


def find_optimal_image_size_and_extend_db(
    db, imdir="processed/train/", out="odir/extended.tsv"
):
    """
    :param db: Directory of data (Directory to images,.xlsx file and later processed data too)
    :param imdir: Directory to cropped images
    :param out: Directory of extended Database (saving as .tsv file)
    :return: Tuple: values for new Image Size
    """
    #imdir = db + imdir

    df = pd.read_excel(db + "odir/ODIR-5K_Training_Annotations(Updated)_V2.xlsx")
    df["Left-Width"] = int(0)
    df["Left-Height"] = int(0)
    df["Right-Width"] = int(0)
    df["Right-Height"] = int(0)

    x = np.zeros_like(df["ID"]).astype("int")
    y = np.zeros_like(df["ID"]).astype("int")
    z = np.zeros_like(df["ID"]).astype("int")
    w = np.zeros_like(df["ID"]).astype("int")

    min_x, min_y = float("inf"), float("inf")
    for i, row in enumerate(df["Left-Fundus"]):
        s = imdir + row
        t = imdir + row.replace("left", "right")
        img = pil.Image.open(s)
        x[i] = img.width
        y[i] = img.height
        if img.width * img.height < min_x * min_y:
            min_x, min_y = img.width, img.height

        img.close
        img = pil.Image.open(t)
        z[i] = img.width
        w[i] = img.height
        img.close

    df["Left-Width"] = x
    df["Left-Height"] = y
    df["Right-Width"] = z
    df["Right-Height"] = w
    print("saving the extended database to: ", db + out)
    df.to_csv(db + out, index=False, sep="\t")

    print("minimal/maximal size (width-height):", (min(x), min(y)), (max(x), max(y))),

    avg_size = np.sum(x) / np.alen(x), np.sum(y) / np.alen(x)
    print("Average size:     Width %i   Height %i" % (avg_size[0], avg_size[1]))

    print("Minimal/Maximal ratio (height/width):", min(y / x), max(y / x))

    ratio_height_width = np.sum(y) / np.sum(x)
    print("Total ratio (left_height/left_width):", ratio_height_width)

    print("\nMinimal image size: %ix%i\n" % (int(min_x), int(min_y)))

    for new_w in range(min_x, int(avg_size[0]), 2):
        for new_h in range(min_y, int(avg_size[1]), 2):
            if ratio_height_width - 0.01 < new_h / new_w < ratio_height_width + 0.01:
                print(
                    "Best minimal image size (close to the average ratio): %ix%i\n"
                    % (new_w, new_h)
                )
                return new_w, new_h


def rotate(img, outdir, fname):
    # Prerequisites for rotating: Only those images should be rotated on which the retina is a 'whole' circle
    # They are defined by the distance between two black pixels (values of these pixels are (0, 0, 0)) in the first
    # and last row respectively the column
    # Max distance is needed and depends on the image size
    def check_prereq(array):
        l = len(array)
        max_distance = 0.225 * l
        min, max = l, 0
        for i, el in enumerate(array):
            if i == 0 or i == l - 1:
                continue

            if i < l // 2:
                prev_el = array[i - 1]
                if (
                    el[0] != 0
                    or el[1] != 0
                    or el[2] != 0
                    and prev_el[0] == 0
                    and prev_el[1] == 0
                    and prev_el[2] == 0
                ):
                    min = i

            if i > l // 2:
                next_el = array[i + 1]
                if (
                    el[0] != 0
                    or el[1] != 0
                    or el[2] != 0
                    and next_el[0] == 0
                    and next_el[1] == 0
                    and next_el[2] == 0
                ):
                    max = i

        return abs(max - min) < max_distance

    if (
        check_prereq(img[0])
        and check_prereq(img[-1])
        and check_prereq(np.transpose(img)[0])
        and check_prereq(np.transpose(img)[-1])
    ):

        angles = [10, -10]  # [20, -15, -10, -5, -2.5, 2.5, 5, 10, 15, 20]
        for angle in angles:
            io.imsave(
                outdir + fname + "_rot_%i.jpg" % angle,
                img_as_ubyte(transform.rotate(img, angle)),
            )
