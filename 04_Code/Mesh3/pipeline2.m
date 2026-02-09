clear all;
close all;
clc;




%plot the mesh
U=4*pi;
V=2*pi;
u=linspace(0,4*pi,50);
v=linspace(0,2*pi,50);
[u,v]=meshgrid(u,v);
r=1;
x=(1.2+(u/10).*cos(v)).*cos(u);
y=(1.2+(u/10).*cos(v)).*sin(u);
z=(u/10).*sin(v)+u/pi;
surf(x,y,z)
hold on

%plot the 3d line
u = linspace(0,4*pi,40)
x=1.2.*cos(u);
y=1.2.*sin(u);
z=u/pi;
plot3(x,y,z,'r');

axis equal