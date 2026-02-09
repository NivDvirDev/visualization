clear all;
close all;
clc;

THETA_0 = 5; % constant
THETA_1 = 10.3; % starting angle
A = 3.762;
B = 0.001317;
C = 7.967;
D = 0.1287;
E = 0.003056;

s=2;
% Calculate (x,y,z) coordinates of points defining the spiral path
theta = THETA_1:5:910.3;
for i = 1:length(theta)
    if (theta(i)<=99.9)
        R(i) = s*C*(1-D*log(theta(i)-THETA_0));
    else
        R(i) = s*A*exp(-B*theta(i));
    end

end

x = R.*cosd(theta);
y = R.*sind(theta);
z = zeros(1,length(theta));
% z = E.*(theta-0);
plot(x,y);
plot3(x,y,z,'g','linewidth',2)

% hold on
% [u,v]=meshgrid(theta,R);
% x=(R+0.5*cos(v)).*cosd(u);
% y=(R+0.5*cos(v)).*sind(u);
% z=0.5*sin(v)+E.*(u-THETA_1);
% mesh(x,y,z,'facecolor','none')
% 
% axis equal