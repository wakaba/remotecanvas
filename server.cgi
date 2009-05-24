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

if ($ENV{REQUEST_METHOD} eq 'POST') {
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
  print q[<!DOCTYPE HTML><html lang=en><title>List</title>];
  print q[<meta name="viewport" content="width=device-width">];
  print q[<ul>];
  print q[<li><a href="client.html?mode=editor">new</a>];

  for my $date (reverse get_dates) {
    printf q[<li>%s <a href="client.html?mode=viewer;date=%s">view</a> <a href="client.html?mode=editor;date=%s">edit</a>],
        (scalar localtime ($date / 1000)),
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
} else {
  print "Content-Type: text/plain\n\n";
  open my $data_file, '<', $data_file_name or die "$0: $data_file_name: $!";
  while (<$data_file>) {
    print $_;
  }
}
