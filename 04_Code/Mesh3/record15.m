function  [cDisplay3AMP , cDisplay3PHAZ]=record15(Song,y,FreqIndex,Freq)
% D = gpuDevice(1);
% reset(D)
% wait(D)
% FreqIndex=5;
fs=Song.SampleRate
dt = 1/fs;
FrameNumberPerSecond=60;
dFrame=1/FrameNumberPerSecond;
m_real=(dFrame/dt)
m=12
[TotalSample stam]=size(y(:,1));  %Song.TotalSample;
TotalSample=round(TotalSample);
TotalFrameNumber=round(TotalSample/m_real);
cDisplay3AMP(FreqIndex,TotalFrameNumber)=0;
cDisplay3PHAZ(FreqIndex,TotalFrameNumber)=0;

y = padarray(y,[(m) 0],0,'both');

pi2m=(2*pi/m);
array=(-pi):pi2m:(pi-pi2m);
array=array.';
preh(FreqIndex)=0;
for i3=1:1:FreqIndex; 
            preh(i3)=(Freq(i3));
end
   disp(['array size: ',num2str(size(array)),'     ','preh size: ',num2str(size(preh))])
preh=((array)*(preh)).';
% % GPU_array=gpuArray(complex(0,array.'));
% % size(preh)
% % GPU_preh=gpuArray(complex(0,preh.'));
% % GPU_preh=((GPU_preh)*(GPU_array));
% GPU_preh=rot90(GPU_preh);
% size(GPU_preh)
% clear GPU_array
GPU_preh=exp(complex(0,preh));  %gpuArray()
size(GPU_preh)
% preh(300,300)
DetectNumber=2;
AMP=(100/((dFrame/dt)*DetectNumber));
AverageSum(FreqIndex)=0;
AverageVector(FreqIndex,DetectNumber)=0;
% AverageVector(FreqIndex)=0;
length(array);
 g(length(array),1)=0;  
disp(['g: ',num2str(size(g))])
 
 start_record=(round(m)+1);
 end_record=(TotalSample-(1.5*m)-1);
 TotalFrameNumber=length(start_record:(m_real):end_record);
 for record=start_record:(m_real):end_record;
     tic

     Detect=1:(m/DetectNumber):(m);
%     for i=1:1:DetectNumber;
%         record+Detect(i)-round(0.5*(m))
%         record+Detect(i)+round(0.5*(m))
%         g(:,i)=y((record+Detect(i)-round(0.5*(m))):(record+Detect(i)+round(0.5*(m))),1);
%         g(:,i)=complex(mean(y((record+Detect(i)-round(0.5*(m))):(record+Detect(i)+round(0.5*(m))),:),2),0);
%     end
%     disp(['ysection: ',num2str(size(complex(mean(y((record-round(0.5*(m))):(record+round(0.5*(m))-1),:),2),0)))])
    g(:)=complex(mean(y((record-round(0.5*(m))):(record+round(0.5*(m))-1),:),2),0);
%     disp(['ysection: ',num2str((record-round(0.5*(m)))),'   ',num2str((record+round(0.5*(m))-1))])
    GPU_g=g(:);  %gpuArray()
%     disp(['g: ',num2str(size(g))])
%      size(GPU_preh);
%       size(GPU_g)
%     size((exp(GPU_preh))*GPU_g)
% vvv=exp(GPU_preh);
% vvv(300,300)
%         reset(D)
%         wait(D)
%     disp(['GPU_preh: ',num2str(size(GPU_preh))]);
%     GPU_preh;
%     disp(['GPU_g: ',num2str(size(GPU_g))]);
%     GPU_g;
    
        GPU=abs((GPU_preh*GPU_g)).*(pi2m*1000);
%         whos GPU_g
        deliver=  GPU  ; %gather()
%         whos deliver
%         disp(['pi2m_15: ',num2str(pi2m)])
        cDisplay3AMP(:,1+round((record-start_record)/m_real))=deliver*AMP;%;
GPU=GPU.*0;
%         cDisplay3PHAZ(:,round(record/m))=imag(cDisplay3);
%         cDisplay3AMP(:,round(record/m))=real(cDisplay3);
%     cDisplay3AMP(:,round(record/m))=gather(  sum(abs((GPU_preh*GPU_g).*(100./(m*DetectNumber))),2)  );
%     cDisplay3PHAZ(:,round(record/m)) = gather(  mean(diff(angle((exp(GPU_preh)*GPU_g).*(100./(m))),1,2),2)  );
%     cDisplay3(:,round(record/m))=cpuArray(real((sum((abs(sum(GPU_g.'*exp(complex(0,GPU_preh)))/m)*100)/DetectNumber,2))));
%   if (round(record/m)==15); 
%     cDisplay3(3,15)
%   end
    
%     cDisplay3(:,round(record/m))=sum((abs(sum(g.'*exp(complex(0,preh)))/m)*100)/DetectNumber,2);

    time = toc;
    disp(['Sample time in seconds: ',num2str(time)])
    disp(['Current Sample number: ',num2str(1+round((record-start_record)/m_real))])
    disp(['Total Samples Record_15: ',num2str(TotalFrameNumber)])

  end
   close all
end
