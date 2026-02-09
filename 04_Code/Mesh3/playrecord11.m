function  [h3]=playrecord11(Song,y,cDisplay9AMP,cDisplay9PHAZ,xDisplay,yDisplay,myjet,Freq, theta, Radius, cDisplay3AMP)


    
     [h3,m,c,TotalFrameNumber,xDisplay,yDisplay,FrameNumberPerSecond, R]=initializeTube(Song,y,xDisplay,yDisplay,myjet,Freq, theta, Radius, cDisplay3AMP);

%      playloop(Song,y,cDisplay9AMP,cDisplay9PHAZ,xDisplay,yDisplay,h3,m,c,TotalFrameNumber,Freq,FrameNumberPerSecond, theta, Radius, R);
%      makemovie(TotalFrameNumber,y,m);
      


end

function [h3,m,c,TotalFrameNumber,xDisplay,yDisplay,FrameNumberPerSecond, R]=initializeTube(Song,y,xDisplay,yDisplay,myjet,Freq, theta, Radius, cDisplay3AMP)
    
     

    fs=Song.SampleRate;
    dt = 1/fs;
    FrameNumberPerSecond=60;
    dFrame=1/FrameNumberPerSecond;
    m=dFrame/dt;
    [TotalSample stam]=size(y(:,1))  %Song.TotalSample; 
    TotalFrameNumber=round(TotalSample/m);
    FreqIndex=length(Freq);

    set(0,'defaultfigurecolor',[0 0 0]);
    fig=figure('Position',[0 0 1280 720]);
%     zoom('off');
    
    t2=atan((yDisplay)./(xDisplay));
    t2=t2.*4.*pi./1.57+4*pi;
    t = linspace(0,8*pi,FreqIndex);
    c = 1:numel(t);      %# colors
    

    size(c)
    c=[c(:)];
    %     size(xDisplay)
    THETA_1 = 10.3; % starting angle
    E = 0.003056;
    s=2;

    InerCircel=31;
    R=linspace(0,2*pi,InerCircel);
% -1.5*(theta(:)/50.2602)
    SRadius=0;
    [u,v]=meshgrid(theta,R);
    x=(Radius+((u/15)).*cos(v)).*cos(u);
    y=(Radius+((u/15)).*cos(v)).*sin(u);
    z=((u/15)+0.1).*sin(v)+(E-exp(u/1000)).*(u-(THETA_1))+50;
    C=zeros(InerCircel,3601,3);
    for i=1:InerCircel;
        C(i,:,:)=myjet(:,:);
    end
    disp(['C:',num2str(size(c))]);
    h3 = mesh(x,y,z,C,'EdgeColor','flat', 'FaceColor','none')
    
    

%     h3.YData=(Radius+((u/15)).*cos(v)).*sin(u);
    tsul=flip(u).*(0.01+0.0015*cDisplay3AMP(:,201)');
    h3.YData=(theta+(tsul).*cos(v)).*sin(u);
    h3.XData=(theta+(tsul).*cos(v)).*cos(u);
%     SuperRadius=flip(Radius).^(1.15);
    h3.ZData=(flip(theta))+(tsul).*(sin(v))-50;
    h3.CData=C;
    % colormap(1-myjet(1:stop,:) );

    size(myjet)
    myjet2=[myjet];
    %myjet2=[myjet(1:length(myjet),:);myjet(1:length(myjet),:)] ; %1-flip(myjet);
    size(myjet2)
    colormap(1-myjet );

     
    zlim([-45 45]);
    az = 0;
    el = 30;
    view(az, el);
    camlight left;
    lighting phong;
    h3.FaceAlpha='flat';
    h3.AlphaData=h3.ZData;
%     disp(['h3.ZData:',num2str(max(h3.ZData))])
    set(gca, 'color', [0 0 0]);
%     set(gca,'xtick',[],'ytick',[],'ztick',[])
%     set(gca,'ZColor',[0 0 0]);
%     set(gca,'YColor',[0 0 0]);
%     set(gca,'XColor',[0 0 0]);
    v = get(h3,'FaceColor');    

    
end


function playloop(Song,y,cDisplay9AMP,cDisplay9PHAZ,xDisplay,yDisplay,h3,m,c,TotalFrameNumber,Freq,FrameNumberPerSecond, theta, Radius, R)
    
 

    sample=0;
    RecordSemple=0;
    FreqIndex=length(Freq);
    
    size(xDisplay)
    r=sqrt(xDisplay(:).^2+yDisplay(:).^2);
    index(FreqIndex)=0; 
    for i3=1:1:FreqIndex; 
       [stam, index(i3)]=min( abs(Freq./2 - Freq(i3)));
    end
    size(index)
    dr=(r(index(:))-r(:)).';
    size(dr)
    alfa=angle(complex(yDisplay(:),xDisplay(:)));
    
    
    % Prepare the new file.
    videoFWriter = vision.VideoFileWriter('C:\check_record15.avi','AudioInputPort',true,'FrameRate',FrameNumberPerSecond);
    videoFWriter.AudioCompressor

    TotalFrameNumber
%     zlim([0 90]);
    az =25;
    el = 90;
    del=0.1;
    
    SRadius=0;
    [u,v]=meshgrid(theta,R);
    
    while ( sample < (TotalFrameNumber-4))% == whilecondition);
        
        RecordSemple=RecordSemple+m;
        sample=round(RecordSemple/m);
        
       
        THETA_1 = 10.3;
        E = 0.003056;
        tsul=flip(u).*(0.01+0.0015*cDisplay9AMP(:,sample)');
        h3.YData=(Radius+(tsul).*cos(v)).*sin(u);
        h3.XData=(Radius+(tsul).*cos(v)).*cos(u);
        h3.ZData=(tsul).*sin(v)+(E-exp(u.*0.005)).*(u-(THETA_1))+10;


%         az = az+0.01;
        az = 45;
%         el = el+0.00005; %-2.5*sin(sample/50);
         if (el > 90-del);
            del=del*(-1);
        end
        if (el < 1+del);
            del=del*(-1);
        end
        el = el+del;
        set(gca,'XLim',[-30 30])
          set(gca,'YLim',[-30 30])
        view( az, el);
%         view( 180*sin(el), 90*abs(el));
        zoom('off');

        set(gca,'CameraTarget',[0 0 -10]);

        set(gca,'CameraViewAngleMode','manual')
        ctarg = get(gca,'CameraTarget');
        cpos = get(gca,'CameraPosition');
        newcp = cpos - 0.40*(cpos - ctarg);
        set(gca,'CameraPosition',newcp);
          
        sample
        F=getframe(gcf);
        step(videoFWriter, F.cdata,y((m*(sample-1)+1):(m*sample)+0,:));

    end
    stop(Song)
    delete(h3);
    sample
    release(videoFWriter);
    close all
 
      
end
