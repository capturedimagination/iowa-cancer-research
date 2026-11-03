from pathlib import Path
import re,json,html,os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Flowable, KeepTogether
from reportlab.lib.enums import TA_LEFT
ROOT=Path(__file__).resolve().parents[1]

def register_report_fonts():
 # Prefer the original fonts when installed; a public checkout needs no Codex runtime.
 home=Path.home()
 font_dirs=[]
 if os.environ.get('IOWA_CANCER_FONT_DIR'):
  font_dirs.append(Path(os.environ['IOWA_CANCER_FONT_DIR']).expanduser())
 runtime_root=home/'.cache/codex-runtimes'
 if runtime_root.is_dir():
  font_dirs.extend(sorted(runtime_root.glob('*/dependencies/native/libreoffice-headless/**/fonts/truetype')))
 font_dirs.extend([home/'Library/Fonts',home/'.local/share/fonts',home/'.fonts',
                   Path('/Library/Fonts'),Path('/System/Library/Fonts'),
                   Path('/usr/local/share/fonts'),Path('/usr/share/fonts')])
 font_dirs=list(dict.fromkeys(directory for directory in font_dirs if directory.is_dir()))
 fonts=[('Body',('LinLibertine_R_G.ttf','LinLibertine_R.ttf'),'Times-Roman'),
        ('Body-Bold',('LinLibertine_RB_G.ttf','LinLibertine_RB.ttf'),'Times-Bold'),
        ('Body-Italic',('LinLibertine_RI_G.ttf','LinLibertine_RI.ttf'),'Times-Italic'),
        ('Head',('Rubik-Regular.ttf',),'Helvetica'),
        ('Head-Bold',('Rubik-Bold.ttf',),'Helvetica-Bold')]
 for name,filenames,fallback in fonts:
  path=next((match for directory in font_dirs for filename in filenames
             for match in sorted(directory.rglob(filename)) if match.is_file()),None)
  if path is None:
   pdfmetrics.registerFont(pdfmetrics.Font(name,fallback,'WinAnsiEncoding'))
  else:
   pdfmetrics.registerFont(TTFont(name,str(path)))

register_report_fonts()
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body-Italic',boldItalic='Body-Bold')
pdfmetrics.registerFontFamily('Head',normal='Head',bold='Head-Bold',italic='Head',boldItalic='Head-Bold')
GREEN=colors.HexColor('#264D46'); INK=colors.HexColor('#242D2B'); GRAY=colors.HexColor('#64716C'); LIGHT=colors.HexColor('#EDF2EF'); RULE=colors.HexColor('#CCD6D0')
styles={
 'body':ParagraphStyle('BodyStyle',fontName='Body',fontSize=10.8,leading=14.25,textColor=INK,spaceAfter=8),
 'title':ParagraphStyle('Title',fontName='Head-Bold',fontSize=38,leading=43,textColor=GREEN,spaceBefore=16,spaceAfter=15),
 'h2':ParagraphStyle('H2',fontName='Head-Bold',fontSize=18,leading=22,textColor=GREEN,spaceAfter=15,keepWithNext=True),
 'h3':ParagraphStyle('H3',fontName='Head-Bold',fontSize=10.8,leading=14,textColor=GREEN,spaceBefore=8,spaceAfter=6,keepWithNext=True),
 'bullet':ParagraphStyle('Bullet',fontName='Body',fontSize=10.7,leading=14,textColor=INK,spaceAfter=6,leftIndent=12,firstLineIndent=0,bulletIndent=0),
 'table':ParagraphStyle('Cell',fontName='Body',fontSize=9.6,leading=12,textColor=INK),
 'th':ParagraphStyle('TH',fontName='Head-Bold',fontSize=8.7,leading=11,textColor=GREEN),
 'ref':ParagraphStyle('Ref',fontName='Body',fontSize=9.3,leading=12,textColor=INK,spaceAfter=7),
}
REFS={x['id']:x for x in json.loads((ROOT/'research/source-index.json').read_text())}

def fmt(s):
 # Normalize typographic dashes for reliable portable glyphs.
 s=s.replace('\u2011','-').replace('\u2013','-').replace('\u2014',' - ').replace('\u00a0',' ')
 s=html.escape(s,quote=False)
 s=re.sub(r'\[([^\]]+)\]\((https?://[^\s]+)\)',lambda m:'<a href="'+m.group(2).replace('"','%22')+'" color="#264D46">'+m.group(1)+'</a>',s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'`([^`]+)`',r'<i>\1</i>',s)
 def cites(m):
  pieces=[]
  for part in m.group(1).split(','):
   part=part.strip(); n=int(part.split('-')[0])
   if n not in REFS: raise ValueError(f'Unknown reference {n}')
   pieces.append(f'<a href="{REFS[n]["url"].replace("&","&amp;")}" color="#43655E">{part}</a>')
  return '<font size="8.2">['+', '.join(pieces)+']</font>'
 return re.sub(r'\[([0-9]+(?:\s*[-,]\s*[0-9]+)*)\]',cites,s)

class RateChart(Flowable):
 def __init__(self): super().__init__();self.width=504;self.height=135
 def draw(self):
  c=self.canv;c.setFont('Head',8);c.setFillColor(GRAY)
  c.drawString(0,124,'AGE-ADJUSTED RATES PER 100,000 / YEAR')
  x0=120;maxw=320;top=101
  rows=[('New cancers: Iowa',504.1,GREEN),('New cancers: U.S.',453.4,colors.HexColor('#9DAFA5')),('Deaths: Iowa',148.2,GREEN),('Deaths: U.S.',143.2,colors.HexColor('#9DAFA5'))]
  for i,(label,v,col) in enumerate(rows):
   y=top-i*23;c.setFont('Body',9);c.setFillColor(INK);c.drawString(0,y+1,label)
   c.setFillColor(col);c.rect(x0,y-1,maxw*v/550,10,fill=1,stroke=0)
   c.setFont('Head',8.4);c.setFillColor(INK);c.drawString(x0+maxw*v/550+7,y,v.__str__())
  c.setStrokeColor(RULE);c.line(x0,15,x0+maxw,15)
  for t in [0,100,200,300,400,500]:
   x=x0+maxw*t/550;c.setFillColor(GRAY);c.setFont('Head',7);c.drawCentredString(x,4,str(t))

class ReportDoc(SimpleDocTemplate):
 def afterFlowable(self,flowable):
  if isinstance(flowable,Paragraph) and flowable.style.name in ['H2','Title']:
   title=flowable.getPlainText();key='section-'+str(self.seq.nextf('bookmark'));self.canv.bookmarkPage(key);self.canv.addOutlineEntry(title,key,0,False)

def decorate(c,doc):
 c.saveState();w,h=doc.pagesize
 c.setFillColor(GREEN);c.setFont('Head-Bold',8);c.drawString(54,h-31,'CANCER IN IOWA')
 c.setFillColor(GRAY);c.setFont('Head',7.5);c.drawRightString(w-54,h-31,'EVIDENCE REVIEW / OCTOBER 2026')
 c.setStrokeColor(RULE);c.setLineWidth(.5);c.line(54,43,w-54,43)
 c.setFont('Head',7.4);c.setFillColor(GRAY);c.drawString(54,29,'Research cutoff: October 22, 2026');c.drawRightString(w-54,29,str(doc.page))
 c.restoreState()

text=(ROOT/'Iowa-Cancer-Research.md').read_text();lines=text.splitlines();story=[];i=0;inrefs=False
while i<len(lines):
 line=lines[i].strip()
 if not line: i+=1;continue
 if line=='<!-- PAGE -->': story.append(PageBreak());i+=1;continue
 if line=='<!-- CHART: rates -->':story.append(Spacer(1,4));story.append(RateChart());i+=1;continue
 if line.startswith('<!--'):i+=1;continue
 if re.match(r'^\[\d+\]:',line):i+=1;continue
 if line.startswith('# '):story.append(Paragraph(fmt(line[2:]),styles['title']));i+=1;continue
 if line.startswith('## '):
  inrefs=line=='## Source register';story.append(Paragraph(fmt(line[3:]),styles['h2']));i+=1;continue
 if line.startswith('### '):story.append(Paragraph(fmt(line[4:]),styles['h3']));i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].strip().startswith('|'):
   cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
   if not all(re.fullmatch(r':?-+:?',x) for x in cells): rows.append(cells)
   i+=1
  n=len(rows[0]);header=' '.join(rows[0]).lower()
  if n==2:weights=[.18,.82]
  elif n==3:
   if 'county' in header:weights=[.38,.31,.31]
   elif 'study' in header:weights=[.31,.36,.33]
   elif 'priority' in header:weights=[.18,.41,.41]
   else:weights=[.42,.22,.36]
  else:
   if 'measure' in header:weights=[.43,.13,.16,.28]
   else:weights=[.43,.14,.14,.29]
  cells=[[Paragraph(fmt(x),styles['th' if ri==0 else 'table']) for x in row] for ri,row in enumerate(rows)]
  t=Table(cells,colWidths=[504*x for x in weights],repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('LINEBELOW',(0,0),(-1,0),.7,GREEN),('LINEBELOW',(0,1),(-1,-1),.35,RULE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
  story.extend([t,Spacer(1,10)]);continue
 if line.startswith('- '):story.append(Paragraph(fmt(line[2:]),styles['bullet'],bulletText='-'));i+=1;continue
 if re.match(r'^\d+\. ',line):
  num,rest=line.split('. ',1);story.append(Paragraph(fmt(rest),styles['bullet'],bulletText=num+'.'));i+=1;continue
 para=[line];i+=1
 while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#','|','<!--','- ')) and not re.match(r'^\[\d+\]:',lines[i].strip()):
  para.append(lines[i].strip());i+=1
 story.append(Paragraph(fmt(' '.join(para)),styles['ref' if inrefs else 'body']))
out=ROOT/'output/pdf/Iowa-Cancer-Research-2026-10-22.pdf';out.parent.mkdir(parents=True,exist_ok=True)
doc=ReportDoc(str(out),pagesize=(612,792),rightMargin=54,leftMargin=54,topMargin=55,bottomMargin=57,title='Cancer in Iowa - Evidence Review, October 22, 2026',author='Research compilation',subject='Iowa cancer burden, contributing risks, prevention, care and sources',allowSplitting=1)
doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
print(out)
