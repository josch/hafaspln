from PIL import Image, ImageDraw

XOFF = 14700
YOFF = 9770
W = 10000
H = 10000

f = open("cities_germany_291009.out.txt")
city, x, y, l = f.readline().split("\t")
min_x = int(x)
max_x = int(x)
min_y = int(y)
max_y = int(y)
for line in f:
    city, x, y, l = line.split("\t")
    if int(x) > max_x:
        max_x = int(x)
    if int(x) < min_x:
        min_x = int(x)
    if int(y) > max_y:
        max_y = int(y)
    if int(y) < min_y:
        min_y = int(y)

print min_x, max_x, min_y, max_y

w = (max_x-min_x)/10000
h = (max_y-min_y)/10000

print w, h

im = Image.new("1", (W, H), 1)
draw = ImageDraw.Draw(im)

f.seek(0)
for line in f:
    city, x, y, l = line.split("\t")
    draw.point(((int(x)-min_x)/100000-XOFF,H-((int(y)-min_y)/100000-YOFF)), fill=0)

im.save("out.png", "PNG")
