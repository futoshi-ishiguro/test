#!/usr/local/bin/ruby --
# #! /home/yamamoto/app/bin/ruby --
# #!/usr/bin/ruby

require 'cgi'
require 'nkf'
require '/usr/local/lib/ruby/gems/1.8/gems/tmail-1.2.7.1/lib/tmail'
#require 'tmail'
require 'net/smtp'
require 'csv'

THIS_CGI = 'entry.cgi'
WEB_ADMIN = 'miaw@ertl.jp'

FROM  = 'cest.secretariat@ertl.jp'
#FROM   = 'miaw@ertl.jp' #�ƥ�����FROM

NFile  = 'number' #���ߥʡ����ÿͿ��򵭲�����ե�����
NFile2 = 'number2' #���Ʋ񻲲ÿͿ��򵭲�����ե�����
#NFile3 = 'number3' #�����ѡ�����ԥ塼�����ز񻲲ÿͿ��򵭲�����ե�����
LFile  = 'list.csv' #�����ԥꥹ��

TITLE  = 'CEST��19�󵻽ѥ��ߥʡ����ÿ���'

LIMIT  = 30 #���Ʋ���� changed 2009/2/10 40 -> 42 (�ƥ��ȷ�+ID66)
LIMIT_MAIN = 80 #���ߥʡ���� changed 2009/2/10: 200->201
#LIMIT  = 3 #�ƥ����Ѥκ��Ʋ����
#LIMIT_MAIN = 4 #�ƥ����ѤΥ��ߥʡ����

MAIN_NOTIFY = 1 #notify_last �ؿ������ ���ߥʡ����üԿ���������
KONSIN_NOTIFY = 2 #notify_last �ؿ������ ���Ʋ񻲲üԿ���������
#SUPERCOM_NOTIFY =3 #notify_last �ؿ������ ̾�祹���ѡ�����ԥ塼�����ز񻲲üԿ���������

ITEMS = %w(num name furi com dept appo email tel zip addr type party  bill free)
ITEM_DESCS = %w(����ID ̾�� �դ꤬�� ���̾ ����̾ ��̾ E-mail���ɥ쥹 �����ֹ� ͹���ֹ� ���� ������� ���Ʋ�  ������̵ͭ ��ͳ������)

#���ߥʡ�������Τߤ�ʬ
COST = {'CEST���' => '3,000',
       # 'ASIF���' => '3,000',
        '����' => '6,000', 
        '����' => '0'}
#���Ʋ���­���줿��(��4000��)
COST2 = {'CEST���' => '7,000',
       # 'ASIF���' => '7,000',
        '����' => '10,000', 
        '����' => '4,000'}

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
    type = Params['type']

    if Params['party'] == '����'
        Params['cost'] = COST2[type]
##        Params['cost_s'] = "�������#{COST[type]}��(�������ޤ�)�Ⱥ��Ʋ��4,000�ߤǹ��#{COST2[type]}�ߤǤ���"
       Params['cost_s'] = "��������#{COST2[type]}�ߤǤ���"
    else
        Params['cost'] = COST[type]
        Params['cost_s'] = "�������#{COST[type]}��(�������ޤ�)�Ǥ���"
    end
end

def verify_input
    err = ''
    if Params['name'].empty?
        err += '̾�������Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['furi'].empty?
        err += '�դ꤬�ʤ����Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['com'].empty?
        err += '���̾�����Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['dept'].empty?
        err += '����̾�����Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['email'].empty?
        err += 'E-mail���ɥ쥹�����Ϥ���Ƥ��ޤ���<br>'
    else
        unless Params['email'] =~ /.@./
            err += 'E-mail���ɥ쥹�������Ǥ���<br>'
        end
    end
    if Params['type'].nil?
        err += '������̤����Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['tel'].empty?
        err += '�����ֹ椬���Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['zip'].empty?
        err += '͹���ֹ椬���Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['addr'].empty?
        err += '���꤬���Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['party'].nil?
        err += '���Ʋ�νз礬���Ϥ���Ƥ��ޤ���<br>'
    end
##    if Params['supercom'].nil?
##        err += '̾�祹���ѡ�����ԥ塼�����ز�νз礬���Ϥ���Ƥ��ޤ���<br>'
##    end
    if Params['bill'].nil?
        err += '������̵ͭ�����Ϥ���Ƥ��ޤ���<br>'
    end
    if Params['email2'] != Params['email']
        err += 'E-mail���ɥ쥹�����פ��Ƥ��ޤ���'
    end
    Params.delete('email2')
    if Params['party'] == '����'
        File.open(NFile2, 'r') {|file2|
        file2.lock {
            num2 = file2.gets.to_i
            if num2 >= LIMIT
                err += '���Ʋ�������ã���ޤ������ᡢ���դ����ڤ�ޤ�����<br>'
                err += '������Ǥ��������Ʋ����ʤˤ��ƺ��٤��������ߤ���������<br>'
                #notify_last(KONSIN_NOTIFY, WEB_ADMIN)
            end
        }
    }
    end
    
    File.open(NFile){|file|
        file.lock{
            num = file.gets.to_i 
            if num >= LIMIT_MAIN
                err = '���ߥʡ����ÿͿ��������ã���ޤ������ᡤ���դ������ڤ�ޤ�����<br>'
                err += '����������ޤ���<br>'
                #notify_last(MAIN_NOTIFY, WEB_ADMIN)
            end
        }
    }
#    File.open(NFile3){|file3|
#        file3.lock{
#            num3 = file3.gets.to_i 
#            if num3 >= LIMIT_MAIN
#                err = '̾�祹���ѡ�����ԥ塼�����ز񻲲ÿͿ��������ã���ޤ������ᡤ���դ������ڤ�ޤ�����<br>'
#                err += '����������ޤ���<br>'
#                #notify_last(SUPERCOM_NOTIFY, WEB_ADMIN)
#            end
#        }
#    }
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
    } + '<br>' + '<form method="POST" action="#{CGI.escapeHTML(THIS_CGI)}">' +
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

            if Params['party'] == '����'
                File.open(NFile2, 'r+') {|file2|
                    file2.lock {
                        num2 = file2.gets.to_i + 1
                        if num2 > LIMIT
                            err = '���Ʋ�������ã���ޤ������ᡢ���դ����ڤ�ޤ�����<br>'
                            err += '������Ǥ��������Ʋ����ʤˤ��ƺ��٤��������ߤ���������<br>'
                            p_html(err)
                            exit
                        elsif num2 == LIMIT
                            notify_last(KONSIN_NOTIFY, WEB_ADMIN)
                        end
                        file2.rewind
                        file2.truncate(0)
                        file2.puts(num2)
                        }
                }
            end

#            if Params['supercom'] == '����'
#                File.open(NFile3, 'r+') {|file3|
#                   file3.lock {
#                        num3 = file3.gets.to_i + 1
#                        if num3 > LIMIT_MAIN
#                            err = '̾�祹���ѡ�����ԥ塼�����ز�������ã���ޤ������ᡢ���դ����ڤ�ޤ�����<br>'
#                            err += '������Ǥ�����̾�祹���ѡ�����ԥ塼�����ز����ʤˤ��ƺ��٤��������ߤ���������<br>'
#                            p_html(err)
#                        elsif num3 == LIMIT_MAIN
#                            notify_last(SUPERCOM_NOTIFY, WEB_ADMIN)
#                        end
#                        file3.rewind
#                        file3.truncate(0)
#                        file3.puts(num3)
#                        }
#                  
#                }
#            end


 
        num = file.gets.to_i + 1
        if num > LIMIT_MAIN
            err = '���ߥʡ����ÿͿ��������ã���ޤ������ᡤ���դ����ڤ�ޤ�����<br>'
            err += '����������ޤ���<br>'
            exit
        elsif num == LIMIT_MAIN
            notify_last(MAIN_NOTIFY, WEB_ADMIN)
        end
        Params['num'] = num
       
        begin
            write_csv
            sendmail(Params['email'])
            sendmail('cest.secretariat@ertl.jp') #�����ߴ�λ����reply�᡼����̳�ɤˤ�����褦���ѹ���2012/11/08��
            p_end
            file.rewind
            file.truncate(0)
            file.puts(num)
#            file3.rewind
#            file3.truncate(0)
#            file3.puts(num3)

        rescue => e
            Params['err'] = e.to_s
            sendmail('miaw@ertl.jp')
            p_html("�᡼��������˼��Ԥ��ޤ�����")
        end
        }

        #�����ã����������web�����Ԥ˥᡼������Ρ�
        #�����������Ķ���Ƥ��ޤä��顤�ޤ��᡼������Ρʤ����̵���Ϥ���
        if num >= LIMIT_MAIN
            notify_last(MAIN_NOTIFY, WEB_ADMIN)
        end
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
����ID #{Params['num']}�Ǽ����դ��ޤ�����<br>
<br>
�������꤬�Ȥ��������ޤ���<br>
��ǧ�Υ᡼����������ޤ���<br>
<br>
#{Params['cost_s']}<br>
2017ǯ5��10���ޤǤˡ��嵭�ζ�ۤ򲼵��θ��¤ˤ�������ߤ���������<br>
�������κݤˤϡ������Ԥ�̾�������˼���ID�����Ϥ��Ƥ���������<br>
��: #{Params['num']} �����ȥ���<br>
<br>
�����衧��ɩ���UFJ��� �ʶ�ͻ���إ����ɡ�0005��<br>
�ܻ���Ź��Ź�֡�670��<br>
�����¶⡡No.3573564<br>
�ȹ��ߥ����ƥ೫ȯ���Ѹ���񡡲�Ĺ�����Ĺ���<br>
���ߥ��ߥ����ƥࡡ�������ҥ���<br>
<br>
<br>
<a href="../index.html">HOME�����</a>
<br>
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
  body = ITEMS.zip(ITEM_DESCS).map {|i, desc| "  %-#{max_desc_len + 2}s#{Params[i]}\n" % desc}
  mail.body = NKF.nkf('-j', <<EOF)
#{Params['name']} ��
    
����CEST���ѥ��ߥʡ���Ͽ��ǧ�񡡢�
�����٤�CEST���ѥ��ߥʡ��ˤ��������ߤ�ĺ���ޤ��Ƥ��꤬�Ȥ��������ޤ���
�ܥ᡼�뤬����ɼ�Ȥʤ�ޤ��Τǡ��ץ��ȥ����Ȥξ塢���������դޤǤ�������������

���Ǥϡ�̾�����դ����������ޤ��Τǡ���̾�ɤ�1�礴�Ѱղ�������

��20��CEST���ѥ��ߥʡ�
������2017ǯ5��17���ʿ��13:00 - 16:15
��ꡧ�����󥯤�����1201��ļ���̾�Ų�������
  ����http://www.winc-aichi.jp/access/

���� ��Ͽ���� ��
#{Params['err']}#{body}

�嵭�����Ƥ���Ͽ���ޤ��������꤬�Ȥ��������ޤ�����

#{Params['cost_s']}
�嵭�ζ�ۤ򲼵��θ��¤ˤ�������ߤ���������
�ʿ�����ߡ��ڡ�2017ǯ5��10����
�������κݤˤϡ������Ԥ�̾�������˼���ID�����Ϥ��Ƥ���������
��: #{Params['num']} �����ȥ���

�����衧��ɩ���UFJ��� �ʶ�ͻ���إ����ɡ�0005��
�ܻ���Ź��Ź�֡�670��
�����¶⡡No.3573564
�ȹ��ߥ����ƥ೫ȯ���Ѹ���񡡲�Ĺ�����Ĺ���
���ߥ��ߥ����ƥࡡ�������ҥ���

��Ͽ���Ƥ��ѹ��������CEST��̳�ɤˤ���礻����������
cest.secretariat@ertl.jp
EOF
  Net::SMTP.start('localhost') {|smtp|
    smtp.send_mail(mail.encoded, FROM, to)  #������Ķ��ǥƥ��Ȥ���Ȥ��ϥ����ȥ�����
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

def notify_last(main_or_konsin, to)
  mail = TMail::Mail.new
  mail.date = Time.now
  mail.from = FROM
  mail.to = to
  mail.mime_version = '1.0'
  mail.set_content_type 'text', 'plain', 'charset' => 'iso-2022-jp'

  subject_str = ''
  notify_str  = ''
  if main_or_konsin == MAIN_NOTIFY
      subject_str = 'CEST���ѥ��ߥʡ����������ڤ��ã��'
      notify_str = <<EOF
      CEST���ѥ��ߥʡ����üԿ��������ڤ����ã���ޤ�����
EOF
  else
      subject_str = 'CEST���ѥ��ߥʡ����Ʋ񻲲������ڤ��ã��'
      notify_str = <<EOF
      CEST���ѥ��ߥʡ����Ʋ�λ��üԿ��������ڤ��ã���ޤ�����
EOF
  end
  mail.subject = NKF.nkf('-jM', subject_str)
  mail.body = NKF.nkf('-j', notify_str)
  Net::SMTP.start('localhost') {|smtp|
    smtp.send_mail(mail.encoded, FROM, to)  #������Ķ��ǥƥ��Ȥ���Ȥ��ϥ����ȥ�����
  }
end

main

