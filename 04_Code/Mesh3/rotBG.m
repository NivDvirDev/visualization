background = imread('/mnt/sdb1/drive_E_backup/background/panorama.jpg');
background = rgb2gray(background);
imshow(background)
angles = 70:30:360;
grayImage = imread('cameraman.tif');
% Get the dimensions of the image.  
% numberOfColorBands should be = 1.
[rows, columns, numberOfColorChannels] = size(grayImage);
if numberOfColorChannels > 1
  % It's not really gray scale like we expected - it's color.
  % Convert it to gray scale by taking only the green channel.
  grayImage = grayImage(:, :, 2); % Take green channel.
end
% Resize background
background = imresize(background, [rows, columns]);
for k = 1 : length(angles)
  % Rotate the image.
  rotatedImage = imrotate(grayImage, angles(k), 'crop');
  % Get a mask.
  mask = rotatedImage == 0;
  mask = bwareafilt(mask, 4);
  % Replace black background with image
  rotatedImage(mask) = background(mask);
  pause(0.6)
  imshow(rotatedImage);
  % Make background the same si
  %     imwrite(J,['hex08',num2str(i),'.jpg'])  
end