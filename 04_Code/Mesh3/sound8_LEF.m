clear all;  close all;    clc;


%[filename, pathname]=uigetfile('*.wav','Select the MATLAB code file');
global SongTag SongPath SongVersion
SongTag='MaskOff';   SongVersion='1';
SongPath='D:\drive_E_backup\MaskOff.wav';
[y0,Fs] =audioread(SongPath);   %   ../Layla_60sec.wav
y = normalize(y0,'range',[-0.5 0.5]);
5207
    
% song = audioplayer(y, Fs);   %data for the song rate     % whilecondition = song.Running;
time=0;
a=1;
N=500;
c(N,N)=0;
colormap hsv
m=500*4;
fs=44100;
dt = 1/fs;
t = (0:m-1)/fs;
n = pow2(nextpow2(m));

t2=0:0.01:24;
r2=t2;
y2=r2.*sin(t2);
x2=r2.*cos(t2);

t3=(pi):((2*pi)/12):((2*pi)*12.5);      %(pi):((2*pi)/12):((2*pi)*10);
length(t3);
Goldenratio=(1+sqrt(5))/2;
r3(25)=0;
r3(1)=2;
r3(11)=r3(1);
FirstRadiusDelta =(0.5+1.1)*(pi)/12;
R = FirstRadiusDelta;
FreqIndex=0;
Freq(500)=0;
RoundFreqIndex=0;
RoundFreq(100)=0;
FourierDisplay(500)=0;
xDisplay(381)=0;    yDisplay(381)=0;    cDisplay(381)=0;

clr = {'b','r'};    cstring='bmkrygcbmkrygc';
mycolormap=0;
length(t3);
RdStart=0.015;
RdEnd=-0.09;
(-(RdStart-RdEnd)/(length(t3)));
Rd=RdStart:(-(RdStart-RdEnd)/(length(t3))):(RdEnd);

for i=12:1:(length(t3)-2)

    r3(i)=r3(i-1)+R;

    R=((1+RdStart)+Rd(i))*R;
%     exp(-i/(length(t3)-12));
%     y3(i)=r3(i)*sin(t3(i));
%     x3(i)=r3(i)*cos(t3(i));
    

    deltat=(pi)/6;
    averager3=(r3(i)+r3(i-1))/2;
    jumplong=0.45;
    sector=0:jumplong:(averager3*deltat);
    lengthsector=length(sector)-1;
    if  ~exist('sectorgap', 'var'); sectorgap=0; end
%      disp(['(averager3*deltat):',num2str((averager3*deltat))])
        

    for i2=sectorgap:jumplong:lengthsector;   
       FreqIndex=FreqIndex+1;
       CurrentRadius=(r3(i-1)+R*i2/lengthsector);
       CurrentAngle=(t3(i-1)+(deltat/lengthsector)*i2);
       Freq(FreqIndex)=(4*(2^( (-(3-1/3)*pi+CurrentAngle)/(2*pi) )));
       Mark='kh';
       xDisplay(FreqIndex)= CurrentRadius*cos(CurrentAngle);
       yDisplay(FreqIndex)= CurrentRadius*sin(CurrentAngle);
       theta(FreqIndex)=CurrentAngle;
       Radius(FreqIndex)=CurrentRadius;
%       plot((averager3+R*i2/lengthsector)*cos(t3(i-1)+(deltat/lengthsector)*i2),(averager3+R*i2/lengthsector)*sin(t3(i-1)+(deltat/lengthsector)*i2),Mark,'MarkerSize',jumplong*5*10,'MarkerFaceColor',sectorcolor(i));
%          text(averager]3*cos(t3(i-1)+(deltat/lengthsector)*i2),averager3*sin(t3(i-1)+(deltat/lengthsector)*i2), [num2str(marker)]);
       hold on
    end
    sectorgap=jumplong-(lengthsector-i2);
      
     sectorcolor(i)=round((mod(i,12)));
      if ((mod(i,12))==11);% && sectorcolor(i-1)=='y');
          RoundFreqIndex=RoundFreqIndex+1; 
          RoundFreq(RoundFreqIndex)=Freq(FreqIndex);
%           disp(['mod(i,12):',num2str(mod(i,12))])
%           disp(['i:',num2str(i)])
%           disp(['sum(mycolormap):',num2str(sum(mycolormap))])
%           disp('---------------------------------------------------')
          mycolormap=[mycolormap(:);FreqIndex-sum(mycolormap-1)];
          
      end
      
    plot(xDisplay,yDisplay,'o'); drawnow;
%     plot(theta(1:end-1),diff(theta))
end


    global  mtheta; mtheta=theta;
    global  mRadius; mRadius=Radius;

    
    
%     [xDisplayIntegral,yDisplayIntegral]=draftTsul(Radius,FreqIndex);
% 
% plot(xDisplayIntegral,yDisplayIntegral,'-'); drawnow;




RoundFreqIndex=RoundFreqIndex+1; 
RoundFreq(RoundFreqIndex)=Freq(FreqIndex);
mycolormap=[mycolormap(:);round((FreqIndex-sum(mycolormap))*1.5)];

myjet(1,3)=0;
 for mycolormapindex=2:1:length(mycolormap)
     myjet=[myjet;hsv(mycolormap(mycolormapindex))];
 end
    myjet=myjet(2:(FreqIndex+1),1:3);
    
    
    close Figure 1;

% % close all;  % % plot(x3,y3)

% % cd techila\lib\Matlab\      % % installsdk()        % % techilainit()


global cDisplay3AMP myFileFullName
% % % %*************** open a .mat file in Matlab ************************
% OpenFrameData


% close all;  [cDisplay3AMP,path]=record15_LEF(SongTag,Fs,y,FreqIndex,Freq,RoundFreqIndex,RoundFreq);   close all;

% % % %*************** save a .mat file in Matlab ************************
% SaveFrameData
OpenFrameData
% [cDisplay5iso226]=iso226sute11(Fs,y,cDisplay3AMP,FreqIndex,Freq,mycolormap,mycolormapindex); close all;

    
h3 = piperecord11_LEF(SongTag,Fs,y0,cDisplay3AMP, myFileFullName,...
                      xDisplay,yDisplay,myjet,Freq, theta, Radius);


    
system(['C:\FFmpeg\bin\ffmpeg -i N:\mat\Project\Mesh\',SongTag, ...
        '.mj2  -i "',SongPath,'"  -strict -2  -aspect 16:9 ',...
        ' -filter:v scale=1280:720 -c:v libx264 -preset ',...
        'slow -crf 10  -c:a copy   -shortest    N:\mat\Project\Mesh\',...
        SongTag,SongVersion,'s.mov  -y'])
    
system(['C:\FFmpeg\bin\ffmpeg -i N:\mat\Project\Mesh\',SongTag, ...
        '.mj2  -i "',SongPath,'"  -strict -2  -aspect 16:9 ',...
        ' -filter:v scale=2560:1440 -c:v libx264 -preset ',...
        'slow -crf 10  -c:a copy   -shortest    N:\mat\Project\Mesh\',...
        SongTag,SongVersion,'.mov  -y'])


    
function OpenFrameData
    global cDisplay3AMP myFileFullName SongTag
    folder = 'N:\mat\Project\Mesh';  % You specify this!
    fullMatFileName = fullfile(folder,  ['cDisplay_',SongTag,'.mat']);
    [cDisplay3AMP ]=load(fullMatFileName,'cDisplay3AMP' ).cDisplay3AMP;
%     [myFileFullName ]=load(fullMatFileName,'path' ).path;
end
function SaveFrameData
    global cDisplay3AMP path SongTag
    folder = 'N:\mat\Project\Mesh';  % You specify this!
    fullMatFileName = fullfile(folder,  ['cDisplay_',SongTag,'.mat']);
    save(fullMatFileName,'cDisplay3AMP' , 'path');
end

    function [xDisplayIntegral,yDisplayIntegral]=draftTsul(Radius,FreqIndex)
    global mtheta
    xDisplayIntegral(FreqIndex)=0;
    yDisplayIntegral(FreqIndex)=0;
        for i_draft=1:FreqIndex
               xDisplayIntegral(i_draft)=(Radius(i_draft)*cos(mtheta(i_draft)))+xDisplayIntegral(Back360(i_draft));
               yDisplayIntegral(i_draft)=(Radius(i_draft)*sin(mtheta(i_draft)))+yDisplayIntegral(Back360(i_draft));
        end
   
    function [prevRoll]=Back360(index)
        prevRoll = closestIndex(mtheta(index)-(2*pi),mtheta);
    end    
    function [closestValue]=closestValue(A,V)
        [minValue,closestIndex] = min(abs(A-V'));
        closestValue = N(closestIndex);
    end
    function [closestIndex]=closestIndex(A,V)
        [minValue,closestIndex] = min(abs(A-V'));
    end
 end
