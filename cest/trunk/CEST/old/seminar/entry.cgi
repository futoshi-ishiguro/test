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
TITLE = 'CEST第9回技術セミナー参加申込'

ITEMS = %w(num name furi zip addr com dept appo tel email type party bill free)
ITEM_DESCS = %w(申込番号 名前 ふりがな 郵便番号 住所 会社名 部署名 役職名 電話番号 E-mailアドレス 会員種別 懇親会 請求書の有無 自由記載欄)
COST = {'CEST会員' => '3,000',
        'コンピュータ応用技術協会員' => '3,000',
        '豊橋商工会議所 電子産業部会員' => '3,000',
        '学生' => '1,000',
        'いずれにも該当せず' => '8,000'}
COST2 = {'CEST会員' => '6,500',
        'コンピュータ応用技術協会員' => '6,500',
        '豊橋商工会議所 電子産業部会員' => '6,500',
        '学生' => '4,500',
        'いずれにも該当せず' => '11,500'}

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
#  管理モード                                                                       #
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
    p_html('パスワードが違います')
  end
  exit
end


#####################################################################################
#                                                                                   #
#  入力モード                                                                       #
#                                                                                   #
#####################################################################################

def input
  mkparams
  verify_input
  p_confirm
end

def mkparams
  Cgi.params.each {|k, v| Params[k] = NKF.nkf('-e', v.to_s)}

  if Params['party'] == '出席'
    Params['cost'] = COST2[Params['type']]
    Params['cost_s'] = "参加費用は#{COST[Params['type']]}円(資料代を含む)と懇親会の3,500円で合計#{COST2[Params['type']]}円です。"
  else
    Params['cost'] = COST[Params['type']]
    Params['cost_s'] = "参加費用は#{COST[Params['type']]}円(資料代を含む)です。"
  end
end

def verify_input
  err = ''
  if Params['name'].empty?
    err += '名前が入力されていません。<br>'
  end
  if Params['email'].empty?
    err += 'E-mailアドレスが入力されていません。<br>'
  else
    unless Params['email'] =~ /.@./
      err += 'E-mailアドレスが不正です。<br>'
    end
  end
  unless err.empty?
    p_html(err)
    exit
  end
end

def p_confirm
  p_html('以下の内容で申込みますか?<br><br>' +
    Cgi.table {
      ITEMS[1..-1].zip(ITEM_DESCS[1..-1]).map {|i, desc|
        Cgi.tr { Cgi.td { CGI.escapeHTML(desc) } + Cgi.td { CGI.escapeHTML(Params[i]) } }
      }
    } + '<br>' + '<form method="POST" action="entry.cgi">' +
    ITEMS[1..-1].map {|i|
      %|<input type="hidden" name="#{i}"  value="#{CGI.escapeHTML(Params[i])}">|
    }.join +
    '<input type="hidden" name="mode" value="confirm">' +
    '<input type="button" value="訂正" onClick="javascript:history.back()">　　' +
    '<input type="submit" value="申込">' +
    '</form>'
    )
end

#####################################################################################
#                                                                                   #
#  確認モード                                                                       #
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
        p_html("メールの送信に失敗しました。")
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
申込ありがとうございます。<br>
確認のメールを送信します。<br>
<br>
#{Params['cost_s']}<br>
上記の金額を下記の口座にお振り込みください。<br>
（振り込み〆切　2006年2月9日）<br>
<br>
振込先：三菱東京UFJ銀行 （金融機関コード：0005）<br>
本山出張所（店番：670）<br>
普通預金　No.3573564<br>
組込みシステム開発技術研究会　会長　高田広章<br>
クミコミシステム　タカダヒロアキ<br>
EOF
end

def sendmail(to)
  mail = TMail::Mail.new
  mail.date = Time.now
  mail.from = FROM
  mail.to = to
  mail.subject = NKF.nkf('-jM', 'CEST技術セミナー申込確認')
  mail.mime_version = '1.0'
  mail.set_content_type 'text', 'plain', 'charset' => 'iso-2022-jp'
  max_desc_len = ITEM_DESCS.map {|i| i.length}.max
  body = ITEMS.zip(ITEM_DESCS).map {|i, desc| "%-#{max_desc_len + 2}s#{Params[i]}\n" % desc}
  mail.body = NKF.nkf('-j', <<EOF)
#{Params['err']}#{body}

上記の内容で登録しました。
ありがとうございました。

#{Params['cost_s']}
上記の金額を下記の口座にお振り込みください。
（振り込み〆切　2006年2月9日）

振込先：三菱東京UFJ銀行 （金融機関コード：0005）
本山出張所（店番：670）
普通預金　No.3573564
組込みシステム開発技術研究会　会長　高田広章
クミコミシステム　タカダヒロアキ

登録内容を変更する場合はCEST事務局にお問合せください。
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
