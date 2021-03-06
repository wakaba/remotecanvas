#!/usr/bin/perl
use strict;
use warnings;

my $param = {};
for (map {[split /=/, $_, 2]} split /[&;]/, $ENV{QUERY_STRING} || '') {
  $param->{$_->[0]} = $_->[1];
}

$param->{mode} ||= '';
die unless $param->{date} =~ /\A[0-9]+\z/ or {list => 1, prev => 1, next => 1}->{$param->{mode}};

my $dir_name = './canvas-data';
my $data_file_name = sprintf '%s/data-%s.txt', $dir_name, $param->{date};
my $data_file_name_pattern = qr[^data-([0-9]+)\.txt$];

sub get_dates () {
  my @date;
  opendir my $dir, $dir_name or die "$0: $dir_name: $!";
  for (readdir $dir) {
    if (/$data_file_name_pattern/) {
      push @date, $1;
    }
  }
  return sort {$a <=> $b} @date;
}

if ($param->{mode} eq '' and $ENV{REQUEST_METHOD} eq 'POST') {
  die if $ENV{CONTENT_LENGTH} > 100_000;

  open my $data_file, '>>', $data_file_name or die "$0: $data_file_name: $!";
  print $data_file 'time,', scalar time, "\x0A";
  read STDIN, my $data, $ENV{CONTENT_LENGTH};
  for (split /;/, $data) {
    print $data_file $_, "\x0A";
  }
  print "Status: 204 No Content\n\n";
} elsif ($param->{mode} eq 'list') {
  print "Content-Type: text/html\n\n";
  print q[<!DOCTYPE HTML><html lang=en><title>List</title>
<meta name="viewport" content="width=device-width">
<style>
  img {
    width: 100px;
    float: left;
  }
  ul {
    margin: 0;
    padding: 0;
  }
  li {
    display: block;
    margin: 0;
    padding: 0;
    clear: left;
  }
  li + li {
    margin-top: 0.3em;
    border-top: gray thin solid;
    padding-top: 0.2em;
  }
</style>];
  print q[<ul>];
  print q[<li><a href="client.html?mode=editor">new</a>];

  for my $date (reverse get_dates) {
    printf q[<li><img src="canvas-data/data-%s.txt.png"> %s <a href="client.html?mode=viewer;date=%s">view</a> <a href="client.html?mode=editor;date=%s">edit</a> <a href="client.html?mode=editor;import-date=%s">clone</a> <a href="canvas-data/data-%s.txt">data</a>],
        $date,
        (scalar localtime ($date / 1000)),
        $date,
        $date,
        $date,
        $date;
  }
  
  print q[</ul>];
} elsif ($param->{mode} eq 'next') {
  for (get_dates) {
    next if $_ <= $param->{date};
    my $mode = $ENV{HTTP_REFERER} =~ /viewer/ ? 'viewer' : 'editor';
    my $url = qq<http://$ENV{SERVER_NAME}$ENV{SCRIPT_NAME}/../client.html?mode=$mode;date=$_>;
    $url =~ s/[^\x21-\x7E]/_/g;
    print "Status: 302 Found\nLocation: $url\n\n";
  }
  print "Status: 302 Found\nLocation: http://$ENV{SERVER_NAME}$ENV{SCRIPT_NAME}/../client.html?mode=editor\n\n";
} elsif ($param->{mode} eq 'prev') {
  my $date;
  for (get_dates) {
    last if $_ >= $param->{date};
    $date = $_;
  }
  if (defined $date) {
    my $mode = $ENV{HTTP_REFERER} =~ /viewer/ ? 'viewer' : 'editor';
    my $url = qq<http://$ENV{SERVER_NAME}$ENV{SCRIPT_NAME}/../client.html?mode=$mode;date=$date>;
    $url =~ s/[^\x21-\x7E]/_/g;
    print "Status: 302 Found\nLocation: $url\n\n";
  } else {
    print "Status: 204 Not Found\n\n";
  }
} elsif ($param->{mode} eq 'png' and $ENV{REQUEST_METHOD} eq 'POST') {
  die if $ENV{CONTENT_LENGTH} > 100_000;

  read STDIN, my $url, $ENV{CONTENT_LENGTH};
  die unless $url =~ s[^data:image/png;base64,][];

  require MIME::Base64;
  my $png = MIME::Base64::decode_base64 ($url);

  open my $data_file, '>', $data_file_name . '.png' or die "$0: $data_file_name.png: $!";
  print $data_file $png;

  my $l_url = qq<http://$ENV{SERVER_NAME}$ENV{SCRIPT_NAME}/../$data_file_name.png>;
  print "Status: 201 Created\nLocation: $l_url\nContent-Type: text/plain\n\n";
} elsif ($param->{mode} eq 'haiku' and $ENV{REQUEST_METHOD} eq 'POST') {
  die if $ENV{CONTENT_LENGTH} > 100_000;

  my $url = $ENV{HTTP_X_DATA_URL};
  unless ($url) {
    read STDIN, $url, $ENV{CONTENT_LENGTH};
  }
  die unless $url =~ s[^data:image/png;base64,][];

  require MIME::Base64;
  my $png = MIME::Base64::decode_base64 ($url);

  my $boundary = '';

  if ($ENV{BOUNDARY}) {
    $boundary = $ENV{BOUNDARY};
  } else {
    $boundary .= [0..9, 'A'..'Z', 'a'..'z']->[rand 62] for 1..30;
    #print "Content-Type: multipart/form-data; boundary=$boundary\x0D\x0A\x0D\x0A";
  }

  my $source = 'Remote Canvas';
  if ($ENV{HTTP_USER_AGENT} =~ /Nintendo DSi/) {
    $source .= ' (DSi)';
  } else {
    $source .= ' (Web)';
  }

  my $body = "--$boundary\x0D\x0AContent-Type: image/png\x0D\x0AContent-Disposition: form-data; name=file; filename=$boundary.png\x0D\x0A\x0D\x0A$png\x0D\x0A--$boundary\x0D\x0AContent-Disposition: form-data; name=source\x0D\x0A\x0D\x0A$source\x0D\x0A--$boundary--\x0D\x0A";
  
  require LWP::UserAgent;
  my $ua = LWP::UserAgent->new;
  my $req = HTTP::Request->new (POST => q<http://h.hatena.ne.jp/api/statuses/update.json>);
  $req->authorization_basic ($ENV{PHP_AUTH_USER}, $ENV{PHP_AUTH_PW});
  $req->content_type ('multipart/form-data; boundary=' . $boundary);
  $req->content ($body);
  my $res = $ua->request ($req);
  warn $req->headers->as_string;
  warn $res->as_string;

  if ($res->is_success) {
    print "Status: 201 Posted\nContent-Type: text/plain\n\n" unless $ENV{VIA_PHP_PROXY};
    print 201;
  } else {
    print "Status: 401 Failed\nContent-Type: text/plain\n\n" unless $ENV{VIA_PHP_PROXY};
    print 401;
  }
} else {
  print "Content-Type: text/plain\n\n";
  open my $data_file, '<', $data_file_name or die "$0: $data_file_name: $!";
  while (<$data_file>) {
    print $_;
  }
}
