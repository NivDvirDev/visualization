function  [cDisplay3AMP,FilesName]=record15_LEF(SongTag,Fs,y,FreqIndex,Freq,RoundFreqIndex,RoundFreq)

fs=Fs;
dt = 1/fs; %time spend between two sound samples
FrameNumberPerSecond=60;
dFrame=1/FrameNumberPerSecond; %time spent between two farme samples
m_real=(dFrame/dt); % number of sounds samples for each frame sample
m = 12000;   % exstra sound samples taken before some specific frame appeared on screen, and after the frame gone
[TotalSample, stam]=size(y(:,1));  %Song.TotalSample;
TotalSample=round(TotalSample/1);
TotalFrameNumber=round(TotalSample/m_real);   %number of frames in the whole song

global cDisplay3AMP
% cDisplay3AMP(FreqIndex,TotalFrameNumber)=0; 
global InerCircel;  InerCircel=60;
% cDisplay3PHAZ(TotalFrameNumber,FreqIndex,InerCircel)=0;
folder = 'N:\mat\Project\Mesh';  % You specify this!
FilesName='myFile';
fullMatFileName = fullfile(folder, [FilesName,'071.mat']);
global matObj
matObj = matfile(fullMatFileName,'Writable',true);
% cDisplay3PHAZ(1).data=zeros(FreqIndex,InerCircel);
% save(fullMatFileName,'cDisplay3PHAZ');
% clear cDisplay3PHAZ;

array=(-pi):(2*pi/m):(pi);
array=rot90(array);
preh(FreqIndex)=0;
for i3=1:1:FreqIndex 
            preh(i3)=(Freq(i3));
end

T(FreqIndex)=0;
for i4=1:1:FreqIndex 
    T(i4)=1/(Freq(i4));
    TBitNum(i4)=T(i4)/dt;
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
% preh2=exp(complex((pi)/2,preh));
global GPU_preh; 
GPU_preh=gpuArray(exp(complex((pi)/2,preh)));  %
[mask,AMP_dynamic]=CreateMask(dt ,Freq,m_real);

% % %  Add-Mask %%%
mask=complex(mask,0);  %gpuArray()
GPU_preh=gather(GPU_preh).*mask;  %gpuArray()
GPU_preh=gpuArray(GPU_preh);


% ShowRGBImage(m,m_real,RoundFreqIndex,RoundFreq,Freq)
            


% preh(300,300)
DetectNumber=1;  %2;
AMP(size(AMP_dynamic))=100;
AMP(:)=(AMP_dynamic(:)/((dFrame/dt)*(DetectNumber^2)));
% AMP=flip(AMP);
AMP=rot90(AMP.*22);
% AMP=(100/((dFrame/dt)*(DetectNumber^2)));
AverageSum(FreqIndex)=0;
AverageVector(FreqIndex,DetectNumber)=0;
% AverageVector(FreqIndex)=0;
length(array);
 g(length(array),DetectNumber)=0;  
meanSpiral(FreqIndex)=0;
% clear cDisplay3PHAZ
% global cDisplay3PHAZ;   
% cDisplay3PHAZ(FreqIndex,TotalFrameNumber,InerCircel)=0;


 for record=(round(0.5*m)+1):(m_real):(TotalSample-(1.5*m)-1)
     tic
    sample=round(record/m_real);
     Detect=1:(m/DetectNumber):(m);
    for i=1:1:DetectNumber
        g(:,i)=complex(mean(y((record+Detect(i)-round(0.5*(m))):(record+Detect(i)+round(0.5*(m))),:),2),0);
    end
    GPU_g=gpuArray(g); clear g;
    
    GPU_g=(GPU_preh*GPU_g);
    deliver=  gather(sum(abs(GPU_g),2))  ; clear GPU_g;
    spiral=deliver.*AMP;    clear deliver;
    cDisplay3AMP(:,sample)=spiral; clear spiral;

%  [meanSpiral]=printcircles(spiral,meanSpiral,sample,Freq,RoundFreq,RoundFreqIndex,Round_Y);
%  [meanSpiral]=printcycle(spiral,meanSpiral,sample,Freq,RoundFreq,RoundFreqIndex,Round_Y);
        
    time = toc;
    disp(num2str(time))
    disp(round(record/m_real))
 end
 save(fullfile('N:\mat\Project\Mesh',  ['cDisplay_',SongTag,'.mat']),'cDisplay3AMP');


reset(gpuDevice(1));
% yg = gpuArray(complex(mean(y,2),0));
global FWF gCircel
pack=100;    packet=(round(0.5*m)+1):(pack*m_real):(TotalSample-(1.5*m)-1);
cDisplay3PHAZ(floor(TotalFrameNumber/pack)).data=zeros(FreqIndex,InerCircel);
for Precord=1:1:(length(packet)-1)
        if ((mod(Precord,10))==1)  
            clear cDisplay3PHAZ;
            fullMatFileName = fullfile(folder,['myFile',sprintf('%03i',Precord),'.mat']);
            clear matObj;
            matObj = matfile(fullMatFileName,'Writable',true);
            disp(['************Creat new file: ','myFile',sprintf('%03i',Precord),'.mat',' ************']);
        end
        Packet=matObj.cDisplay3PHAZ(1,Precord);
        try
          FWF=gpuArray(complex(Packet.data,0));
        catch ME 
          if strcmp(ME.identifier, 'MATLAB:complex:invalidRealPartInput')
             disp(['ME.identifier: ',ME.identifier]);
             FWF=gpuArray(Packet.data);
          else
             FWF=gpuArray(zeros(pack,FreqIndex,InerCircel));
          end
        end
        disp(['max-Packet.data: ',num2str(max(Packet.data,[],'all'))]);
        %gpuArray(zeros(pack,FreqIndex,InerCircel));
        OpenPack_sample=round(packet(Precord)/m_real);
        for record= packet(Precord):(m_real):(packet(Precord+1)-m_real)
             tic;    sample=round(record/m_real);

            gCircel=complex(mean(y((record-round(0.5*(m))):(record+round(0.5*(m))),:),2),0);
%             gCircel=yg((record-round(0.5*(m))):(record+round(0.5*(m))));
            printcycle(T,TBitNum,FreqIndex,1+sample-OpenPack_sample,cDisplay3AMP(:,sample));
            time = toc;    disp(['time: ',num2str(time),'     sample: ',num2str(sample),'     max-FWF: ',num2str(max(abs(FWF(1+sample-OpenPack_sample,:,:)),[],'all'))]);
        end
        tic;    %matObj.cDisplay3PHAZ(OpenPack_sample:sample,:,:) = gather(FWF(1:(1+sample-OpenPack_sample),:,:));
        Packet.data = gather(FWF(1:(1+sample-OpenPack_sample),:,:));
%         clear FWF;
        disp(['max-Packet.data: ',num2str(max(Packet.data,[],'all'))]);
        Packet.OpenPack_sample=OpenPack_sample;
        Packet.sample=sample;
        Packet.Precord=Precord;
%         save(fullMatFileName,'cDisplay3PHAZ');
        matObj.cDisplay3PHAZ(1,Precord)=Packet;
        clear Packet;
        time = toc;    disp(['************load the file: ',num2str(time),' ************']);

end
 
   close all
end


function [mask,AMP_dynamic]=CreateMask(dt ,Freq,m_real)
            global GPU_preh  middlePic
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
end

function ShowRGBImage(m,m_real,RoundFreqIndex,RoundFreq,Freq)
            global GPU_preh  middlePic
            [L,W]=size(GPU_preh);
            myRGBImage(L,W,3)=0;
            % G(L,W)=0;
            % B(L,W)=0;
            % B(:,:)=1;
            myRGBImage(:,:,3)=gather(real(GPU_preh));
            Image=image(myRGBImage);   %,'CDataMapping','scaled'
            drawnow
            % myImage=imshow(real(GPU_preh.*mask),[]);
            DrawLine
            
    function DrawLine
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
    end
    drawnow
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
 
 function printcycle(T,TBitNum,FreqIndex,sample,spiral)     
       global  InerCircel gCircel FWF    
       
       for myfreq=1:FreqIndex
           if (spiral(myfreq)>4)
                    dc=round(TBitNum(myfreq));
                    lg=length(gCircel);   cycle=floor(lg/dc);
                    WaveForm=reshape(gCircel(1:(lg-(mod(lg,dc)))),cycle,dc);
                    meanWave=sum(WaveForm,1)./cycle;
                    FWF(sample,myfreq,:)=interp1( (1:1:dc), meanWave, linspace(1, dc,InerCircel )); 
                    clear meanWave dc;
%                 disp([num2str(myfreq),'     ',num2str(length(DWaveForm)),'     ',num2str(spiral(myfreq))])             
           end
       end
       
       
%        pause(1)
%                    DWaveForm=decimate(meanWave,r,min(82,r),'fir');       
%         bit=1:1:length(g); Indx_meanWave=1:length(g)/length(meanWave):length(g) ;
%         plt1=plot(bit,g,'g--',Indx_meanWave ,meanWave,'r*');
%         ax = gca;
%         xticks(0:TBitNum(myfreq):length(g));
%         ax.XGrid = 'on';
%         ax.YGrid = 'off';
%         drawnow


end
