x =.0001+(-4:.2:4);
y = -3:.2:3;
[yy,xx] = meshgrid(y,x);
r = pi*sqrt(xx.^2+yy.^2);
z = sin(r)./r;
bcs = csapi({x,y}, z);
fnplt(bcs)
axis([-5 5 -5 5 -.5 1])