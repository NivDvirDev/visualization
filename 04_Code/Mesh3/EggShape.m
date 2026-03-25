clear all;  close all;    clc;


xpi=pi/44
t = -1:0.01:1;
H = 1;
x = (1-1/pi).*cos(t./pi).*sin(t);
y = -cos(t);
fill(x, y, [1, 0.87, 0.68])
% plot(x, y); drawnow;
axis square
axis([-1, 1, -1, 1]);
axis off
close all; 


plot(t, cos(t./pi)); drawnow;
axis square
axis([-1, 1, -1, 1]);
axis off

for p =1:-0.01:0 %0.42:0.001:0.58

r=(1-1/pi)/3;  


% x = (r.*cos(t./pi)).^(p).*sin(t);
% y = -(r/2).^(1-p).*cos(t);

y = -(r.*cos(t)).^(p).*sin(t.*pi);
x = (r/3).^(1-p).*cos(t.*pi);


% x = (r.*cos(t)).^(p).*sin(t.*pi);
% y = -(r.*cos(t)).^(1-p).*cos(t.*pi);
    
    
% x = cos(t.*((1-p)/pi)).*(sin(t)).^(1-(p/pi));
% y = -cos(t.*(1/p)).*(sin(t)).^(pi-(pi/p));   
    
% x = ((1-pi/p)+(1-1/p)).*cos(t./p).*sin(t+pi/2);
% y = -(1/p-p/pi).*cos(t./(1+(pi-p)).*sin(pi/2);
% fill(x, y, [1, 0.87, 0.68])
% plot(x, y);
fill(x, y, [1, 0.87, 0.68])
axis square
axis([-2, 2, -2, 2]);
axis off
drawnow;
p
% pause(0.001);
end

% h3.EdgeAlpha=0.5;
%     h3.FaceColor = 'interp';
%     h3.FaceAlpha = 0.1.5;