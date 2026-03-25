% classdef LableText
%    enumeration
%       Freqs, Scientific_designation, Name, Octave_name
%    end
% %    methods
% %       function tf = isMeetingDay(obj)
% %          tf = LableText.ne;
% %       end
% %    end
% end

classdef WeekDays
   enumeration
      Monday, Tuesday, Wednesday, Thursday, Friday
   end
   methods
      function tf = isMeetingDay(obj)
         tf = WeekDays.Tuesday == obj;
      end
   end
end


% today = WeekDays.Tuesday;
% today.isMeetingDay


% s=LableText.Freqs;
        
% switch plottype
%     case 'Freqs' 
%         Solfege(note).label(octave).ts.TextData=string([num2str(Solfege(note).Freqs(octave),4),'Hz']);
%     case 'Scientific_designation' 
%         Solfege(note).label(octave).ts.TextData=string(Solfege(note).Scientific_designation(octave));
%     case 'Name' 
%         Solfege(note).label(octave).ts.TextData=string(Solfege(note).Name);
%     case 'Octave_name'
%         Solfege(note).label(octave).ts.TextData=string(Solfege(1).Octave_name(octave));
%     otherwise
%         warning('Unexpected plot type. No plot created.')
% end