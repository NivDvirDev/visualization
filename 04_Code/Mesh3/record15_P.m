function  [cDisplay3AMP , cDisplay3PHAZ]=record15_P(Song,y,FreqIndex,Freq)
D = gpuDevice(1);
reset(D)
% wait(D)
fs=Song.SampleRate;
dt = 1/fs; %time spend between two sound samples
FrameNumberPerSecond=60;
dFrame=1/FrameNumberPerSecond; %time spent between two farme samples
m_real=(dFrame/dt); % number of sounds samples for each frame sample
m = 12000;   % exstra sound samples taken before some specific frame appeared on screen, and after the frame gone
[TotalSample, stam]=size(y(:,1));  %Song.TotalSample;
TotalSample=round(TotalSample/1);
TotalFrameNumber=round(TotalSample/m_real);   %number of frames in the whole song
cDisplay3AMP(FreqIndex,TotalFrameNumber)=0;
cDisplay3PHAZ(FreqIndex,TotalFrameNumber)=0;

array=(-pi):(2*pi/m):(pi);
array=rot90(array);
preh(FreqIndex)=0;
for i3=1:1:FreqIndex; 
            preh(i3)=(Freq(i3));
end
size(preh);
size(array);
preh=((array)*(preh)).';
% % GPU_array=gpuArray(complex(0,array.'));
% % size(preh)
% % GPU_preh=gpuArray(complex(0,preh.'));
% % GPU_preh=((GPU_preh)*(GPU_array));
% GPU_preh=rot90(GPU_preh);
% size(GPU_preh)
% clear GPU_array
GPU_preh=gpuArray(exp(complex((pi)/2,preh)));
size(GPU_preh)
% preh(300,300)
DetectNumber=2;
AMP=(100/((dFrame/dt)*(DetectNumber^2)));
AverageSum(FreqIndex)=0;
AverageVector(FreqIndex,DetectNumber)=0;
% AverageVector(FreqIndex)=0;
length(array);
 g(length(array),DetectNumber)=0;  


 for record=(round(0.5*m)+1):(m_real):(TotalSample-(1.5*m)-1)
     tic

     Detect=1:(m/DetectNumber):(m);
    for i=1:1:DetectNumber
%         record+Detect(i)-round(0.5*(m))
%         record+Detect(i)+round(0.5*(m))
%         g(:,i)=y((record+Detect(i)-round(0.5*(m))):(record+Detect(i)+round(0.5*(m))),1);
        g(:,i)=complex(mean(y((record+Detect(i)-round(0.5*(m))):(record+Detect(i)+round(0.5*(m))),:),2),0);
%         g(:,i)=complex(y((record+Detect(i)-round(0.5*(m))):(record+Detect(i)+round(0.5*(m))),1),0);
    end
    GPU_g=gpuArray(g);
%      size(GPU_preh);
%       size(GPU_g)
%     size((exp(GPU_preh))*GPU_g)
% vvv=exp(GPU_preh);
% vvv(300,300)
%         reset(D)
%         wait(D)
    
        GPU_g=(GPU_preh*GPU_g);
        deliver=  gather(sum(abs(GPU_g),2))  ;
        cDisplay3AMP(:,round(record/m_real))=deliver*AMP;

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
    disp(num2str(time))
    disp(round(record/m_real))
  end
   close all
end
