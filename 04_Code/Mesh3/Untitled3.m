Bsin=sin(B);
% dBsin=diff(Bsin(1:end));
% size(Bsin)
% size(dBsin)
for i=1:1000
    dBsin=diff(Bsin)/6217;
    Bsin(2:end)=Bsin(2:end)+Bsin(2:end).*dBsin;
    plot(B(2:end),dBsin,'*b',B(2:end),Bsin(2:end),'*r')
    Bsin(3000)
    pause(0.01)
end
