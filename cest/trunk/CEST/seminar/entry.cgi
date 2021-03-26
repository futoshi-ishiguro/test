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
#FROM   = 'miaw@ertl.jp' #テスト用FROM

NFile  = 'number' #セミナー参加人数を記憶するファイル
NFile2 = 'number2' #懇親会参加人数を記憶するファイル
#NFile3 = 'number3' #スーパーコンピュータ見学会参加人数を記憶するファイル
LFile  = 'list.csv' #申込者リスト

TITLE  = 'CEST第19回技術セミナー参加申込'

LIMIT  = 30 #懇親会定員 changed 2009/2/10 40 -> 42 (テスト君+ID66)
LIMIT_MAIN = 80 #セミナー定員 changed 2009/2/10: 200->201
#LIMIT  = 3 #テスト用の懇親会定員
#LIMIT_MAIN = 4 #テスト用のセミナー定員

MAIN_NOTIFY = 1 #notify_last 関数用定数 セミナー参加者数締切通知
KONSIN_NOTIFY = 2 #notify_last 関数用定数 懇親会参加者数締切通知
#SUPERCOM_NOTIFY =3 #notify_last 関数用定数 名大スーパーコンピュータ見学会参加者数締切通知

ITEMS = %w(num name furi com dept appo email tel zip addr type party  bill free)
ITEM_DESCS = %w(受付ID 名前 ふりがな 会社名 部署名 役職名 E-mailアドレス 電話番号 郵便番号 住所 会員種別 懇親会  請求書の有無 自由記載欄)

#セミナー参加費のみの分
COST = {'CEST会員' => '3,000',
       # 'ASIF会員' => '3,000',
        '一般' => '6,000', 
        '学生' => '0'}
#懇親会費が足された額(＋4000円)
COST2 = {'CEST会員' => '7,000',
       # 'ASIF会員' => '7,000',
        '一般' => '10,000', 
        '学生' => '4,000'}

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
    type = Params['type']

    if Params['party'] == '出席'
        Params['cost'] = COST2[type]
##        Params['cost_s'] = "参加費は#{COST[type]}円(資料代を含む)と懇親会の4,000円で合計#{COST2[type]}円です。"
       Params['cost_s'] = "参加費合計#{COST2[type]}円です。"
    else
        Params['cost'] = COST[type]
        Params['cost_s'] = "参加費は#{COST[type]}円(資料代を含む)です。"
    end
end

def verify_input
    err = ''
    if Params['name'].empty?
        err += '名前が入力されていません。<br>'
    end
    if Params['furi'].empty?
        err += 'ふりがなが入力されていません。<br>'
    end
    if Params['com'].empty?
        err += '会社名が入力されていません。<br>'
    end
    if Params['dept'].empty?
        err += '部署名が入力されていません。<br>'
    end
    if Params['email'].empty?
        err += 'E-mailアドレスが入力されていません。<br>'
    else
        unless Params['email'] =~ /.@./
            err += 'E-mailアドレスが不正です。<br>'
        end
    end
    if Params['type'].nil?
        err += '会員種別が入力されていません。<br>'
    end
    if Params['tel'].empty?
        err += '電話番号が入力されていません。<br>'
    end
    if Params['zip'].empty?
        err += '郵便番号が入力されていません。<br>'
    end
    if Params['addr'].empty?
        err += '住所が入力されていません。<br>'
    end
    if Params['party'].nil?
        err += '懇親会の出欠が入力されていません。<br>'
    end
##    if Params['supercom'].nil?
##        err += '名大スーパーコンピュータ見学会の出欠が入力されていません。<br>'
##    end
    if Params['bill'].nil?
        err += '請求書の有無が入力されていません。<br>'
    end
    if Params['email2'] != Params['email']
        err += 'E-mailアドレスが一致していません。'
    end
    Params.delete('email2')
    if Params['party'] == '出席'
        File.open(NFile2, 'r') {|file2|
        file2.lock {
            num2 = file2.gets.to_i
            if num2 >= LIMIT
                err += '懇親会は定員に達しましたため、受付を締切りました。<br>'
                err += 'お手数ですが、懇親会を欠席にして再度お申し込みください。<br>'
                #notify_last(KONSIN_NOTIFY, WEB_ADMIN)
            end
        }
    }
    end
    
    File.open(NFile){|file|
        file.lock{
            num = file.gets.to_i 
            if num >= LIMIT_MAIN
                err = 'セミナー参加人数が定員に達しましたため，受付を締め切りました．<br>'
                err += '申し訳ありません．<br>'
                #notify_last(MAIN_NOTIFY, WEB_ADMIN)
            end
        }
    }
#    File.open(NFile3){|file3|
#        file3.lock{
#            num3 = file3.gets.to_i 
#            if num3 >= LIMIT_MAIN
#                err = '名大スーパーコンピュータ見学会参加人数が定員に達しましたため，受付を締め切りました．<br>'
#                err += '申し訳ありません．<br>'
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
    p_html('以下の内容で申込みますか?<br><br>' +
           Cgi.table {
        ITEMS[1..-1].zip(ITEM_DESCS[1..-1]).map {|i, desc|
        Cgi.tr { Cgi.td { CGI.escapeHTML(desc) } + Cgi.td { CGI.escapeHTML(Params[i]) } }
    }
    } + '<br>' + '<form method="POST" action="#{CGI.escapeHTML(THIS_CGI)}">' +
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

            if Params['party'] == '出席'
                File.open(NFile2, 'r+') {|file2|
                    file2.lock {
                        num2 = file2.gets.to_i + 1
                        if num2 > LIMIT
                            err = '懇親会は定員に達しましたため、受付を締切りました。<br>'
                            err += 'お手数ですが、懇親会を欠席にして再度お申し込みください。<br>'
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

#            if Params['supercom'] == '出席'
#                File.open(NFile3, 'r+') {|file3|
#                   file3.lock {
#                        num3 = file3.gets.to_i + 1
#                        if num3 > LIMIT_MAIN
#                            err = '名大スーパーコンピュータ見学会は定員に達しましたため、受付を締切りました。<br>'
#                            err += 'お手数ですが、名大スーパーコンピュータ見学会を欠席にして再度お申し込みください。<br>'
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
            err = 'セミナー参加人数が定員に達しましたため，受付を締切りました．<br>'
            err += '申し訳ありません．<br>'
            exit
        elsif num == LIMIT_MAIN
            notify_last(MAIN_NOTIFY, WEB_ADMIN)
        end
        Params['num'] = num
       
        begin
            write_csv
            sendmail(Params['email'])
            sendmail('cest.secretariat@ertl.jp') #申込み完了時にreplyメールを事務局にも送るように変更（2012/11/08）
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
            p_html("メールの送信に失敗しました。")
        end
        }

        #定員に達した時点でweb管理者にメールで通知．
        #万が一定員を超えてしまったら，またメールで通知（これは無いはず）
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
受付ID #{Params['num']}で受け付けました。<br>
<br>
申込ありがとうございます。<br>
確認のメールを送信します。<br>
<br>
#{Params['cost_s']}<br>
2017年5月10日までに，上記の金額を下記の口座にお振り込みください。<br>
お振込の際には、振込者の名前の前に受付IDを入力してください。<br>
例: #{Params['num']} セストタロウ<br>
<br>
振込先：三菱東京UFJ銀行 （金融機関コード：0005）<br>
本山支店（店番：670）<br>
普通預金　No.3573564<br>
組込みシステム開発技術研究会　会長　高田広章<br>
クミコミシステム　タカダヒロアキ<br>
<br>
<br>
<a href="../index.html">HOMEへ戻る</a>
<br>
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
  body = ITEMS.zip(ITEM_DESCS).map {|i, desc| "  %-#{max_desc_len + 2}s#{Params[i]}\n" % desc}
  mail.body = NKF.nkf('-j', <<EOF)
#{Params['name']} 様
    
■　CEST技術セミナー登録確認書　■
この度はCEST技術セミナーにお申し込みを頂きましてありがとうございます。
本メールが参加票となりますので、プリントアウトの上、当日会場受付までご持参下さい。

会場では、名札をお付けいただきますので、お名刺を1枚ご用意下さい。

第20回　CEST技術セミナー
日時：2017年5月17日（水）13:00 - 16:15
場所：ウインクあいち1201会議室（名古屋駅前）
  　　http://www.winc-aichi.jp/access/

　○ 登録内容 ○
#{Params['err']}#{body}

上記の内容で登録しました。ありがとうございました。

#{Params['cost_s']}
上記の金額を下記の口座にお振り込みください。
（振り込み〆切　2017年5月10日）
お振込の際には、振込者の名前の前に受付IDを入力してください。
例: #{Params['num']} セストタロウ

振込先：三菱東京UFJ銀行 （金融機関コード：0005）
本山支店（店番：670）
普通預金　No.3573564
組込みシステム開発技術研究会　会長　高田広章
クミコミシステム　タカダヒロアキ

登録内容を変更する場合はCEST事務局にお問合せください。
cest.secretariat@ertl.jp
EOF
  Net::SMTP.start('localhost') {|smtp|
    smtp.send_mail(mail.encoded, FROM, to)  #ローカル環境でテストするときはコメントアウト
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
      subject_str = 'CEST技術セミナー参加締め切り数達成'
      notify_str = <<EOF
      CEST技術セミナー参加者数が締め切り数に達しました．
EOF
  else
      subject_str = 'CEST技術セミナー懇親会参加締め切り数達成'
      notify_str = <<EOF
      CEST技術セミナー懇親会の参加者数が締め切りに達しました．
EOF
  end
  mail.subject = NKF.nkf('-jM', subject_str)
  mail.body = NKF.nkf('-j', notify_str)
  Net::SMTP.start('localhost') {|smtp|
    smtp.send_mail(mail.encoded, FROM, to)  #ローカル環境でテストするときはコメントアウト
  }
end

main

