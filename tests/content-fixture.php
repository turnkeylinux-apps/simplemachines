<?php

if (PHP_SAPI !== 'cli' || $argc < 2) {
    fwrite(STDERR, "Usage: content-fixture.php create TOKEN | cleanup BOARD_ID TOPIC_ID\n");
    exit(2);
}

chdir('/var/www/simplemachines');
$_SERVER['REMOTE_ADDR'] = '127.0.0.1';
$_SERVER['SERVER_ADDR'] = '127.0.0.1';
$_SERVER['SERVER_NAME'] = 'localhost';
$_SERVER['SERVER_PORT'] = '443';
$_SERVER['REQUEST_METHOD'] = 'GET';
$_SERVER['REQUEST_URI'] = '/index.php';
$_SERVER['REQUEST_URL'] = '/index.php';
$_SERVER['QUERY_STRING'] = '';
$_SERVER['HTTP_HOST'] = 'localhost';
$_SERVER['HTTP_USER_AGENT'] = 'TurnKey-SMF-Acceptance/1.0';
$_SERVER['HTTPS'] = 'on';
$_SERVER['is_cli'] = true;
$_SERVER['SCRIPT_NAME'] = '/index.php';
$_SERVER['PHP_SELF'] = '/index.php';

require_once 'SSI.php';
$ssi_on_error_method = function () use (&$context) {
    fwrite(STDERR, "Simple Machines API error: " . strip_tags($context['error_message']) . "\n");
    exit(1);
};

if ($argv[1] === 'create') {
    if ($argc !== 3 || !preg_match('/^[a-z0-9-]+$/', $argv[2])) {
        fwrite(STDERR, "Invalid fixture token\n");
        exit(2);
    }

    $token = $argv[2];
    $request = $smcFunc['db_query']('', '
        SELECT b.id_cat, b.member_groups, b.id_profile, m.id_member,
               m.member_name, m.email_address
        FROM {db_prefix}boards AS b
        CROSS JOIN {db_prefix}members AS m
        WHERE m.member_name = {string:admin}
        ORDER BY b.id_board
        LIMIT 1', array('admin' => 'admin'));
    $seed = $smcFunc['db_fetch_assoc']($request);
    $smcFunc['db_free_result']($request);
    if (!$seed) {
        throw new RuntimeException('Unable to find the admin and seed board');
    }

    // The board API builds its tree through the current user's visibility
    // query. Run the fixture with the same administrator identity proven by
    // the preceding HTTPS login instead of the guest identity SSI defaults to
    // for a new CLI session.
    $user_info['id'] = (int) $seed['id_member'];
    $user_info['username'] = $seed['member_name'];
    $user_info['name'] = $seed['member_name'];
    $user_info['email'] = $seed['email_address'];
    $user_info['groups'] = array(1);
    $user_info['is_guest'] = false;
    $user_info['is_admin'] = true;
    $user_info['can_manage_boards'] = true;
    $user_info = array_merge($user_info, build_query_board($user_info['id']));
    $context['user']['id'] = $user_info['id'];
    $context['user']['is_guest'] = false;
    $context['user']['is_admin'] = true;

    require_once $sourcedir . '/Subs-Boards.php';
    require_once $sourcedir . '/Subs-Post.php';

    $boardName = 'TurnKey acceptance board ' . $token;
    $topicSubject = 'TurnKey acceptance topic ' . $token;
    $topicBody = 'TurnKey acceptance body ' . $token;
    $boardId = createBoard(array(
        'board_name' => $boardName,
        'move_to' => 'bottom',
        'target_category' => (int) $seed['id_cat'],
        'access_groups' => array_map('intval', explode(',', $seed['member_groups'])),
        'profile' => (int) $seed['id_profile'],
        'inherit_permissions' => false,
    ));
    if (!$boardId) {
        throw new RuntimeException('Simple Machines did not create the board');
    }

    $msgOptions = array(
        'subject' => $topicSubject,
        'body' => $topicBody,
        'icon' => 'xx',
        'smileys_enabled' => true,
        'approved' => 1,
        'send_notifications' => false,
    );
    $topicOptions = array('id' => 0, 'board' => $boardId);
    $posterOptions = array(
        'id' => (int) $seed['id_member'],
        'name' => $seed['member_name'],
        'email' => $seed['email_address'],
        'ip' => '127.0.0.1',
    );
    if (!createPost($msgOptions, $topicOptions, $posterOptions)) {
        throw new RuntimeException('Simple Machines did not create the topic');
    }

    echo "board_id={$boardId}\n";
    echo "topic_id={$topicOptions['id']}\n";
    echo "message_id={$msgOptions['id']}\n";
    echo "board_name={$boardName}\n";
    echo "topic_subject={$topicSubject}\n";
    echo "topic_body={$topicBody}\n";
    exit(0);
}

if ($argv[1] === 'cleanup' && $argc === 4) {
    $boardId = filter_var($argv[2], FILTER_VALIDATE_INT);
    $topicId = filter_var($argv[3], FILTER_VALIDATE_INT);
    if (!$boardId || !$topicId) {
        fwrite(STDERR, "Invalid fixture identifiers\n");
        exit(2);
    }

    require_once $sourcedir . '/RemoveTopic.php';
    require_once $sourcedir . '/Subs-Boards.php';
    removeTopics(array($topicId), true, true);
    deleteBoards(array($boardId));
    echo "cleanup=complete\n";
    exit(0);
}

fwrite(STDERR, "Unknown fixture action\n");
exit(2);
