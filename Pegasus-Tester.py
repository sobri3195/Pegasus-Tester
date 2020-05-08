#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Python script that uses SST - Web Test Framework and the headless WebKit PhantomJS to run functional tests. Made by Muhammad Sobri Maulana'''

__version__ = "1.0"

import os
import re
import glob
import datetime
import csv
import xml.etree.ElementTree as ET

# Variables
EMAIL_FROM      = ''
EMAIL_TO        = ['']
sst_path        = '/usr/local/bin'
sst_bin         = 'sst-run'
sst_num_process = '3'                        # Jumlah tes yang harus dijalankan sekaligus
sst_dir         = 'web_tests'                # Direktori yang menyimpan tes dan hasil
sst_tests       = 'tests'                    # ama direktori yang berisi tes
sst_stats       = 'statistics'               # Direktori tempat statistik akan disimpan untuk setiap domain
sst_options     = ' -q -s -c ' + sst_num_process + ' -r xml -b PhantomJS -d ' + sst_tests

def send_mail_attach(subject, text, files=[]):
  """Kirim email dengan subjek, teks, dan lampiran yang diberikan"""
  assert type(files)==list
  msg            = MIMEMultipart()
  msg['From']    = EMAIL_FROM
  msg['To']      = ', '.join(EMAIL_TO)
  msg['Subject'] = subject
  msg.attach( MIMEText(text) )
  for f in files:
      part = MIMEBase('application', "octet-stream")
      part.set_payload( open(f,"rb").read() )
      Encoders.encode_base64(part)
      part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
      msg.attach(part)
  server = smtplib.SMTP(EMAIL_SERVER)
  server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
  server.quit()

# Kami memperluas PATH sehingga skrip berfungsi di lingkungan crontab
if not re.search(sst_path, os.environ['PATH']):
  os.environ['PATH'] = os.environ['PATH'] + ':' + sst_path

# Kami pindah ke direktori sst dan meluncurkan perintah
os.chdir(sst_dir)
os.system(sst_bin + sst_options)

# Kami mendapatkan total hasilnya
tree           = ET.parse('results/results.xml')
root           = tree.getroot()
total_failures = root.get('failures')
total_tests    = root.get('tests')
total_time     = root.get('time')

# Kami menyiapkan email untuk dikirim jika ada kesalahan
subject = '[Web tests] {0} web tests failed'.format(total_failures)
message = 'RESULT: {0} fails of {1} tests (Time: {2})\n\n'.format(total_failures,total_tests,total_time)

# Kami memeriksa bahwa direktori statistik ada
if not os.path.isdir(sst_stats):
  os.mkdir(sst_stats, 0755)

# Kami menganalisis tes
for test in root.findall('testcase'):
  name   = test.get('name')
  time   = test.get('time')
  # Kami menyimpan statistik untuk setiap tes
  stats  = open(sst_stats + '/' + name + '.csv', "a")
  writer = csv.writer(stats, delimiter=',')
  writer.writerow([datetime.datetime.now(), time])
  stats.close()
  # Kami memeriksa apakah ada tes yang gagal
  fail = test.findall('failure')
  # Jika ada kesalahan kami menyimpan kesalahan
  if fail:
    error   = re.search('AssertionError: (.*)', fail[0].text).group(1)
    message += "TEST: {0} (Time: {1})\nERROR: {2}\n\n".format(name, time, error)

# Jika ada kesalahan, kami mengirim email dengan pesan kesalahan dan pengambilan halaman
if int(total_failures) > 0:
  screenshots = glob.glob('results/*.png')
  print message
  send_mail_attach(subject, message, screenshots)
