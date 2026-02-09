echo 'start crop the wav file'
ffmpeg -y -ss 14 -t 230 -i '/media/niv/New Volume/drive_E_backup/Tones and I - DanceMomkey.wav'     '/media/niv/New Volume/drive_E_backup/DanceMomkey_shortversion.wav'

#echo start Extreme cooling
#sudo /usr/bin/ec4Linux.py enable

echo start running sound8_LEF
sudo -u niv matlab -batch sound8_LEF

echo start ffmpeg sound8_LEF
ffmpeg -i /home/niv/DanceMomkey2.mj2  -i '/media/niv/New Volume/drive_E_backup/DanceMomkey_shortversion.wav'  -strict -2  -aspect 16:9 -filter:v scale=2560:1440 -c:v libx264 -preset slow -crf 10  -c:a copy   -shortest    test_DanceMomkey.mov  -y  
# 3840:2160 , 1280:720


echo start copyng avi
cp test_DanceMomkey.mov   /home/niv/Desktop/test_DanceMomkey.mov

#echo stop Extreme cooling
#sudo /usr/bin/ec4Linux.py disable
