#!/usr/bin/perl
# L1 SpamAssassin worker: loads the rules once, then scores messages read from stdin.
# Protocol: a line with the byte count, then the RFC 822 bytes; one JSON line answers each message.
# The first line written is a header with the versions and the active scoreset.
use strict;
use warnings;
use JSON::PP;
use Mail::SpamAssassin;

my $sa = Mail::SpamAssassin->new({
    local_tests_only   => 1,                # no DNS, RBL, URIBL, Razor, Pyzor or DCC lookups
    dont_copy_prefs    => 1,
    userprefs_filename => '/dev/null',      # no per-user preferences
    userstate_dir      => '/tmp/sa-state',  # nothing persists between runs
    # Static scoring only: no Bayes and no learning from the messages we score (README 5.4).
    post_config_text   => "use_bayes 0\nbayes_auto_learn 0\n",
});
$sa->compile_now(0);

my $json = JSON::PP->new->canonical;
$| = 1;
print $json->encode({
    version  => Mail::SpamAssassin::Version(),
    scoreset => $sa->{conf}->get_score_set(),
}), "\n";

while (defined(my $len = <STDIN>)) {
    chomp $len;
    my $got = read(STDIN, my $raw, $len);
    die "short read: expected $len bytes, got $got\n" unless $got == $len;
    my $mail   = $sa->parse($raw);
    my $status = $sa->check($mail);
    my %hits   = map { $_ => $sa->{conf}->{scores}->{$_} + 0 } split /,/, $status->get_names_of_tests_hit();
    print $json->encode({
        score    => $status->get_score() + 0,
        required => $status->get_required_score() + 0,
        hits     => \%hits,
    }), "\n";
    $status->finish;
    $mail->finish;
}
