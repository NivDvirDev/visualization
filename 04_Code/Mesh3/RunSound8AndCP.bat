echo 'start crop the wav file'
C:\FFmpeg\bin\ffmpeg -y -ss 14 -t 30 -i "D:\drive_E_backup\Tones and I - DanceMomkey.wav"     "D:\drive_E_backup\DanceMomkey_shortversion.wav"

#echo start Extreme cooling
#sudo /usr/bin/ec4Linux.py enable

echo start running sound8_LEF
matlab -batch sound8_LEF

echo start ffmpeg sound8_LEF
C:\FFmpeg\bin\ffmpeg -i N:\mat\Project\Mesh\DanceMomkey2.mj2  -i "D:\drive_E_backup\Tones and I - DanceMomkey.wav"  -strict -2  -aspect 16:9 -filter:v scale=2560:1440 -c:v libx264 -preset slow -crf 10  -c:a copy   -shortest    N:\mat\Project\Mesh\test_DanceMomkey.mov  -y  
# 3840:2160 , 1280:720

#Merge two videos with transparency in ffmpeg
ffmpeg    -i "C:\Users\dvirn\Videos\Los Emigrantes-Ayelet Chen.mp4"  -i  "C:\Users\dvirn\Videos\2021-03-18-2010-38.mp4" -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=480x360[top];   [1:v]setpts=PTS-STARTPTS, scale=480x360, format=yuva420p,colorchannelmixer=aa=0.5[bottom];   [top][bottom]overlay=shortest=1"  -acodec  aac -vcodec libx264 C:\Users\dvirn\Videos\out.mp4

ffmpeg -loop 1 -i image.jpg -i audio.wav -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest out.mp4

#echo start copyng avi
#cp test_DanceMomkey.mov   N:\mat\Project\Mesh\test_DanceMomkey.mov

#echo stop Extreme cooling
#sudo /usr/bin/ec4Linux.py disable
