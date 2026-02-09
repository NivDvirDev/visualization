% a= imread('C:\Users\dvirn\Desktop\dead-sea-1930742_19203.png');
% I=rgb2gray(a);
% % imgTrans = I';
% % iD conversion
% img1D = I(:);
% % Decimal to Hex value conversion
% imgHex = dec2hex(img1D);
% % New txt file creation
% fid = fopen('im16_1.txt', 'wt');
% % Hex value write to the txt file
% fprintf(fid, '00', img1D);
% % Close the txt file
% fclose(fid)
% 
% a=imread('C:\Users\dvirn\Desktop\dead-sea-1930742_19203.png');
% % disp(a);
% for i=1:256 
%     for j=1:256 
%         b(i,j,:) = dec2bi(a(i,j),8);
%         disp(b);
%     end
% end


img= imread('C:\Users\dvirn\Desktop\dead-sea-1930742_19203.png');
img = rgb2gray(img);
imshow(img);
% size(img)
dlmwrite('image.txt', img, 'precision', '%03d');
imgnew = dlmread('image.txt','delimiter','%03d');
size(imgnew)
imgnew=uint8(imgnew);
imshow(imgnew);
imwrite(imgnew,'C:\Users\dvirn\Desktop\dead-sea-1930742_19203_new.png');

%%

imgnew = dlmread('C:\Users\dvirn\Desktop\Yelement102_dirt.txt','%03d');
size(imgnew)
imgnew=uint8(imgnew);
imshow(imgnew);
imwrite(imgnew,'C:\Users\dvirn\Desktop\dead-sea-1930742_19203_new.png');