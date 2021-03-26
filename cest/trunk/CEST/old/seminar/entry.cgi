#!/home/yamamoto/bin/ruby

require 'cgi'
require 'nkf'
require 'tmail'
require 'net/smtp'
require 'csv'

FROM  = 'cest-secretariat@ertl.jp'
#FROM  = 'yamamoto@ertl.jp'
NFile = 'number'
LFile = 'list.csv'
TITLE = 'CEST��9�󵻽ѥ��ߥʡ����ÿ���'

ITEMS = %w(num name furi zip addr com dept appo tel email type party bill free)
ITEM_DESCS = %w(�����ֹ� ̾�� �դ꤬�� ͹���ֹ� ���� ���̾ ����̾ ��̾ �����ֹ� E-mail���ɥ쥹 ������� ���Ʋ� ������̵ͭ ��ͳ������)
COST = {'CEST���' => '3,000',
        '����ԥ塼�����ѵ��Ѷ����' => '3,000',
        '˭��������Ľ� �Żһ��������' => '3,000',
        '����' => '1,000',
        '������ˤ⳺������' => '8,000'}
COST2 = {'CEST���' => '6,500',
        '����ԥ塼�����ѵ��Ѷ����' => '6,500',
        '˭��������Ľ� �Żһ��������' => '6,500',
        '����' => '4,500',
        '������ˤ⳺������' => '11,500'}

Cgi = CGI.new('html4')
Params = {}

class File
  def lock
    begin
      self.flock(File::LOCK_EX)
      yield
    ensure
      self.flock(File::LOCK_UN)
    end
  end
end

def main
  case Cgi['mode']
  when 'admin'
    admin
  when 'input'
    input
  when 'confirm'
    confirm
  end
end


#####################################################################################
#                                                                                   #
#  �����⡼��                                                                       #
#                                                                                   #
#####################################################################################

def admin
  crypted = 'xx'
  File.open('passwd') {|file|
    crypted = file.gets.chomp
  }
  pass = Cgi['pass']
  if pass.crypt(crypted) == crypted
    Cgi.out('type' => 'application/octet-stream',
            'Content-Disposition' => 'attachment; filename=CEST.csv') {
            IO.read(LFile)
    }
  else
    p_html('�ѥ���ɤ��㤤�ޤ�')
  end
  exit
end


#####################################################################################
#                                                                                   #
#  ���ϥ⡼��                                                                       #
#                                                                                   #
#####################################################################################

def input
  mkparams
  verify_input
  p_confirm
end

def mkparams
  Cgi.params.each {|k, v| Params[k] = NKF.nkf('-e', v.to_s)}

  if Params['party'] == '����'
    Params['cost'] = COST2[Params['type']]
    Params['cost_s'] = "�������Ѥ�#{COST[Params['type']]}��(�������ޤ�)�Ⱥ��Ʋ��3,500�ߤǹ��#{COST2[Params['type']]}�ߤǤ���"
  else
    Params['cost'] = COST[Params['type']]
    Params['cost_s'] = "�������Ѥ�#{COST[Params['type']]}��(�������ޤ�)�Ǥ���"
  end
end

def verify_input
  err = ''
  if Params['name'].empty?
    err += '̾�������Ϥ���Ƥ��ޤ���<br>'
  end
  if Params['email'].empty?
    err += 'E-mail���ɥ쥹�����Ϥ���Ƥ��ޤ���<br>'
  else
    unless Params['email'] =~ /.@./
      err += 'E-mail���ɥ쥹�������Ǥ���<br>'
    end
  end
  unless err.empty?
    p_html(err)
    exit
  end
end

def p_confirm
  p_html('�ʲ������Ƥǿ����ߤޤ���?<br><br>' +
    Cgi.table {
      ITEMS[1..-1].zip(ITEM_DESCS[1..-1]).map {|i, desc|
        Cgi.tr { Cgi.td { CGI.escapeHTML(desc) } + Cgi.td { CGI.escapeHTML(Params[i]) } }
      }
    } + '<br>' + '<form method="POST" action="entry.cgi">' +
    ITEMS[1..-1].map {|i|
      %|<input type="hidden" name="#{i}"  value="#{CGI.escapeHTML(Params[i])}">|
    }.join +
    '<input type="hidden" name="mode" value="confirm">' +
    '<input type="button" value="����" onClick="javascript:history.back()">����' +
    '<input type="submit" value="����">' +
    '</form>'
    )
end

#####################################################################################
#                                                                                   #
#  ��ǧ�⡼��                                                                       #
#                                                                                   #
#####################################################################################

def confirm
  mkparams

  File.open(NFile, 'r+') {|file|
    file.lock {

      num = file.gets.to_i + 1
      Params['num'] = num

      begin
        write_csv
        sendmail(Params['email'])
        p_end
        file.rewind
        file.truncate(0)
        file.puts(num)

      rescue => e
        Params['err'] = e.to_s
        sendmail('yamamoto@ertl.jp')
        p_html("�᡼��������˼��Ԥ��ޤ�����")
      end
    }
  }
end


def write_csv
  File.open(LFile, 'a') {|file|
    file.lock {
      CSV::Writer.generate(file, ?,, "\r\n") {|writer|
        writer << (ITEMS.map {|i| Params[i]}.map {|i| NKF.nkf('-s', i.to_s)} + [Params['cost']])
      }
    }
  }
end

def p_end
  p_html(<<EOF)
�������꤬�Ȥ��������ޤ���<br>
��ǧ�Υ᡼����������ޤ���<br>
<br>
#{Params['cost_s']}<br>
�嵭�ζ�ۤ򲼵��θ��¤ˤ�������ߤ���������<br>
�ʿ�����ߡ��ڡ�2006ǯ2��9����<br>
<br>
�����衧��ɩ���UFJ��� �ʶ�ͻ���إ����ɡ�0005��<br>
�ܻ���ĥ���Ź�֡�670��<br>
�����¶⡡No.3573564<br>
�ȹ��ߥ����ƥ೫ȯ���Ѹ���񡡲�Ĺ�����Ĺ���<br>
���ߥ��ߥ����ƥࡡ�������ҥ���<br>
EOF
end

def sendmail(to)
  mail = TMail::Mail.new
  mail.date = Time.now
  mail.from = FROM
  mail.to = to
  mail.subject = NKF.nkf('-jM', 'CEST���ѥ��ߥʡ�������ǧ')
  mail.mime_version = '1.0'
  mail.set_content_type 'text', 'plain', 'charset' => 'iso-2022-jp'
  max_desc_len = ITEM_DESCS.map {|i| i.length}.max
  body = ITEMS.zip(ITEM_DESCS).map {|i, desc| "%-#{max_desc_len + 2}s#{Params[i]}\n" % desc}
  mail.body = NKF.nkf('-j', <<EOF)
#{Params['err']}#{body}

�嵭�����Ƥ���Ͽ���ޤ�����
���꤬�Ȥ��������ޤ�����

#{Params['cost_s']}
�嵭�ζ�ۤ򲼵��θ��¤ˤ�������ߤ���������
�ʿ�����ߡ��ڡ�2006ǯ2��9����

�����衧��ɩ���UFJ��� �ʶ�ͻ���إ����ɡ�0005��
�ܻ���ĥ���Ź�֡�670��
�����¶⡡No.3573564
�ȹ��ߥ����ƥ೫ȯ���Ѹ���񡡲�Ĺ�����Ĺ���
���ߥ��ߥ����ƥࡡ�������ҥ���

��Ͽ���Ƥ��ѹ��������CEST��̳�ɤˤ���礻����������
cest-secretariat@ertl.jp
EOF
  Net::SMTP.start('localhost') {|smtp|
    smtp.send_mail(mail.encoded, FROM, to)
  }
end

def p_html(str)
  Cgi.out('charset' => 'euc-jp') {
    Cgi.html {
      Cgi.head { Cgi.title {TITLE} } +
      Cgi.body {
        str
      }
    }
  }
end

main
