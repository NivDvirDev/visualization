function  [cDisplay3AMP , cDisplay3PHAZ]=record15_LE(Fs,y,FreqIndex,Freq,RoundFreqIndex,RoundFreq)

fs=Fs;
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
for i3=1:1:FreqIndex 
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
preh2=exp(complex((pi)/2,preh));
GPU_preh=gpuArray(exp(complex((pi)/2,preh)));
[L,W]=size(GPU_preh);
mask(L,W)=1;
AMP_dynamic(L)=0;
middlePic=(W-1)/2;
m_effective=flip(normalize(Freq.^(2),'range',[(1/Freq(end))/dt   (W/2)]));
for l=1:1:L
    border=m_real/2;         %max(min(m_effective(l),W/2),m_real/2)
    AMP_dynamic(l)=(100/W)*(2*border);
    for w=1:1:W 
            pixel=(W/2)-w;        gain=border/pixel;
            if abs(gain)<1
                 if gain>0;      mask(l,w)=0+abs(gain);     end    %      left side
                 if gain<0;      mask(l,w)=0+abs(gain);                       end    %      right side
            else
                 mask(l,w)=2-(1/abs(gain));  %      1;
            end
    end
%     for w=round(W/2+m_real/2):1:W;  mask(l,w)=0;  end
end
% imshow(mask)
size(real(GPU_preh.*mask));
myRGBImage(L,W,3)=0;
% G(L,W)=0;
% B(L,W)=0;
% B(:,:)=1;
myRGBImage(:,:,3)=gather(real(GPU_preh.*mask));
Image=image(myRGBImage);   %,'CDataMapping','scaled'
drawnow
% myImage=imshow(real(GPU_preh.*mask),[]);
for i=0:1:floor(m/2/m_real)
    m_X=middlePic-round(m_real/2)-i*m_real;
    myColumn(i+1) = images.roi.Line(gca,'Position',[m_X    0;m_X    L],'Label',['-',num2str(i),'.5'],'LineWidth',1);
end
myLine = images.roi.Line(gca,'Position',[middlePic+m_real/2    0;middlePic+m_real/2    L],'Label',"+1/2",'LineWidth',1);
Round_Y(RoundFreqIndex)=0;
for i=1:RoundFreqIndex
    Round_Y(i)=find(Freq==RoundFreq(i), 1 );
    myRow(i)=images.roi.Line(gca,'Position',[0    Round_Y(i);W    Round_Y(i)],'Label',['Round No. ',num2str(i),'      frequency: ',num2str(RoundFreq(i))],'LineWidth',1);
end
preh2=preh2.*mask;
mask=gpuArray(complex(mask,0));
GPU_preh=GPU_preh.*mask;
% imshow(GPU_preh);
% preh(300,300)
DetectNumber=1;  %2;
AMP(size(AMP_dynamic))=100;
AMP(:)=(AMP_dynamic(:)/((dFrame/dt)*(DetectNumber^2)));
close all;
% AMP=flip(AMP);
AMP=rot90(AMP.*22);
% AMP=(100/((dFrame/dt)*(DetectNumber^2)));
AverageSum(FreqIndex)=0;
AverageVector(FreqIndex,DetectNumber)=0;
% AverageVector(FreqIndex)=0;
length(array);
 g(length(array),DetectNumber)=0;  
meanSpiral(FreqIndex)=0;


 for record=(round(0.5*m)+1):(m_real):(TotalSample-(1.5*m)-1)
     tic
    sample=round(record/m_real);
     Detect=1:(m/DetectNumber):(m);
    for i=1:1:DetectNumber
        g(:,i)=complex(mean(y((record+Detect(i)-round(0.5*(m))):(record+Detect(i)+round(0.5*(m))),:),2),0);
    end
    GPU_g=gpuArray(g);

    
    
%         for i2=1:1:L
% %            myRGBImage(i2,:,2)=(abs(preh2(i2,:))').*g(:,1) + (abs(preh2(i2,:))').*g(:,2);
% %            myRGBImage(i2,:,2)=gather( (abs(GPU_preh(i2,:))').*GPU_g(:,1) + (abs(GPU_preh(i2,:))').*GPU_g(:,2) );
%            myRGBImage(i2,:,2)=gather( (abs(GPU_preh(i2,:)').*GPU_g(:,1)));    % + (abs(GPU_preh(i2,:)').*GPU_g(:,2)) 
%         end
%         Image.CData=myRGBImage;
%         drawnow
        
        GPU_g=(GPU_preh*GPU_g);
        deliver=  gather(sum(abs(GPU_g),2))  ;
        spiral=deliver.*AMP;
        cDisplay3AMP(:,round(record/m_real))=spiral;
        
%         [meanSpiral]=printcircles(spiral,meanSpiral,sample,Freq,RoundFreq,RoundFreqIndex,Round_Y);
        

    time = toc;
    disp(num2str(time))
    disp(round(record/m_real))
 end
  

 
 
 
   close all
end


 function [meanSpiral]=printcircles(spiral,meanSpiral,sample,Freq,RoundFreq,RoundFreqIndex,Round_Y)     
        meanSpiral=( meanSpiral.*(sample-1)+spiral)./sample;
        for i=1:(RoundFreqIndex-1)
            circ=rescale(Freq(Round_Y(i):Round_Y(i+1)),(i-1)*1000,i*1000);
            spir=spiral(Round_Y(i):Round_Y(i+1));
            mSpir=meanSpiral(Round_Y(i):Round_Y(i+1));
            plt1=plot(circ,spir,'g--',circ,mSpir);
            hold on
        end

%         plt1=plot(Freq,spiral);
        xticks(0:1000:(RoundFreqIndex-1)*1000); xticklabels(RoundFreq(1:RoundFreqIndex));
        ylim([0 32]);
        grid on
        hold off
        drawnow
end