function  playrecord15(Song,y,cDisplayAMP,cDisplayPHAZ,xDisplay,yDisplay,myjet,Freq,DestinationFileName, DestinationPathName)


    
     [h3,m_real,c,TotalFrameNumber,FrameNumberPerSecond]=initialize(Song,y,xDisplay,yDisplay,myjet,Freq);
      playloop(Song,y,cDisplayAMP,cDisplayPHAZ,xDisplay,yDisplay,h3,m_real,c,TotalFrameNumber,Freq,FrameNumberPerSecond,DestinationFileName, DestinationPathName);
%      makemovie(TotalFrameNumber,y,m);
      


end

function [h3,m_real,c,TotalFrameNumber,FrameNumberPerSecond]=initialize(Song,y,xDisplay,yDisplay,myjet,Freq)
    
     

    fs=Song.SampleRate;
    dt = 1/fs;
    FrameNumberPerSecond=60;
    dFrame=1/FrameNumberPerSecond;
    m_real=dFrame/dt;
    m=12000;
    [TotalSample stam]=size(y(:,1));  %Song.TotalSample; 
    TotalFrameNumber=round(TotalSample/m_real);
    FreqIndex=length(Freq);

    set(0,'defaultfigurecolor',[0 0 0]);
    fig=figure('Position',[0 0 800 600]);
    zoom('off');
    
    t2=atan((yDisplay)./(xDisplay));
    t2=t2.*4.*pi./1.57+4*pi;
    t = linspace(0,8*pi,FreqIndex);
    c = 1:numel(t);      %# colors
    

            size(c);
    c=[c(:)];
    %     size(xDisplay)

h3 = scatter([xDisplay(:)], [yDisplay(:)],1, ...
        [c(:)],'MarkerEdgeColor','flat','MarkerFaceColor','none');
    
    size(myjet);
    myjet2=[myjet;myjet];
    %myjet2=[myjet(1:length(myjet),:);myjet(1:length(myjet),:)] ; %1-flip(myjet);
    size(myjet2);
    colormap(1-myjet );

     
    zlim([0 90]);
    az = 180;
    el = 90;
    view(az, el);
    camlight left;
    lighting phong
% 
%     set(gca, 'color', [0 0 0]);
%     set(gca,'xtick',[],'ytick',[],'ztick',[])
%     set(gca,'ZColor',[0 0 0]);
%     set(gca,'YColor',[0 0 0]);
%     set(gca,'XColor',[0 0 0]);
%     v = get(h3,'MarkerFaceColor');    
%     set(gca,'ZColor',[0 0 0]);

end

function playloop(Song,y,cDisplayAMP,cDisplayPHAZ,xDisplay,yDisplay,h3,m_real,c,TotalFrameNumber,Freq,FrameNumberPerSecond,DestinationFileName, DestinationPathName)
    
 

    sample=0;
    RecordSemple=0;
    FreqIndex=length(Freq);
    xDisplaySlope(FreqIndex)=0;
    yDisplaySlope(FreqIndex)=0;
    
    % Prepare the new file.
    fullDestinationFileName = fullfile(DestinationPathName, DestinationFileName);
    videoFWriter = vision.VideoFileWriter(fullDestinationFileName,'AudioInputPort',true,'FrameRate',FrameNumberPerSecond);
    videoFWriter.AudioCompressor;
    
    
    size(xDisplay);
    r=sqrt(xDisplay(:).^2+yDisplay(:).^2);
    index(FreqIndex)=0; 
    for i3=1:1:FreqIndex; 
       [stam, index(i3)]=min( abs(Freq./2 - Freq(i3)));
    end
    size(index);
    dr=(r(index(:))-r(:)).';
    size(dr);
    alfa=angle(complex(yDisplay(:),xDisplay(:)));
    betaMax=pi/4;
    beta=betaMax:-((betaMax)/FreqIndex):((betaMax)/FreqIndex);

%     az =0.11;
%     el = 0.21;
%     del=0.00015;
    i3=1:1:FreqIndex; 
    while ( sample < (TotalFrameNumber-4))% == whilecondition);
        
        RecordSemple=RecordSemple+m_real;
        sample=round(RecordSemple/m_real);
        
% 
%        xDisplaySP=[xDisplay(:);(xDisplay(:)-0.01*dr(:).*sin(alfa(:)))].';
%        yDisplaySP=[yDisplay(:);(yDisplay(:)-0.01*dr(:).*cos(alfa(:)))].';
%        
       

       
       
%        delete(h3);
%        line=real(cDisplayAMP(:,sample));
      
%         length(beta);
%         length(alfa);
%        xDisplaySlope(:)=xDisplay(:).*(1+line(:).*cos(beta(:))*0.01);
%        yDisplaySlope(:)=yDisplay(:).*(1+line(:).*cos(beta(:))*0.01);
%        lineA=0.2*([(0*line(:));(line(:).*sin(beta(:)))].');
% 
% 
%        lineB=((0).*lineA(:));
%        length_line=length(real(cDisplayAMP(:,sample)));
%        lineA(length_line)=1;
%        lineB(length_line)=1;
% 
%        lineA(length_line+1)=1;
%        lineB(length_line+1)=1;
       
       AmpStrech=1.0;
%********************************************************************main-print**********************************************
%         h3 = surface([xDisplaySP(:)*AmpStrech, [xDisplay(:);xDisplaySlope(:)]*AmpStrech], [yDisplaySP(:)*AmpStrech, [yDisplay(:);yDisplaySlope(:)]*AmpStrech],[ lineB(:),lineA(:)], ...
%         [c(:), c(:)], 'EdgeColor','flat', 'FaceColor','none','LineWidth',1,'AlignVertexCenters','on'); 
%****************************************************************************************************************************
% newset = h3.SizeData;


set(h3,'SizeData', (1*((real(cDisplayAMP(:,sample))))).^2+0.001)
 refreshdata(h3)
%********************************************************************second-print**********************************************
%         h3 = scatter([xDisplay(:)*AmpStrech], [yDisplay(:)*AmpStrech],[line(:)], ...
%         [c(:)],'MarkerEdgeColor','flat','MarkerFaceColor','none'); 
%****************************************************************************************************************************

% 
%           set(gca,'XLim',[-100 100])
%           set(gca,'YLim',[-100 100])
% 
% 
%          if (el > 0.31);
%             del=del*(-1);
%         end
%         if (el < 0.2);
%             del=del*(-1);
%         end
%         el = el+del;
%         view( 180*sin(az), 90*abs(el));
%         set(gca,'CameraTarget',[0 0 10]);
% 
%         set(gca,'CameraViewAngleMode','manual')
%         ctarg = get(gca,'CameraTarget');
%         cpos = get(gca,'CameraPosition');
%         newcp = cpos - 0.60*(cpos - ctarg);
%         set(gca,'CameraPosition',newcp);
          
%         disp( ['sample: ',num2str(sample)]);
        F=getframe(gcf,[0 0 800 600]);
        step(videoFWriter, F.cdata,y((m_real*(sample-1)+1):(m_real*sample)+0,:));


    end
    stop(Song)
    delete(h3);
    
    release(videoFWriter);
    close all
 
      
end
