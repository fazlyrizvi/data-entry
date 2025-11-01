Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
        'Access-Control-Max-Age': '86400',
        'Access-Control-Allow-Credentials': 'false'
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const requestData = await req.json();
        const { channel, recipient, message, subject, config, notificationId } = requestData;

        if (!channel || !recipient || !message) {
            throw new Error('Channel, recipient, and message are required parameters');
        }

        let sendResult;
        const startTime = Date.now();

        // Send notification based on channel type
        switch (channel) {
            case 'telegram':
                sendResult = await sendTelegramMessage(recipient, message, config);
                break;
            case 'discord':
                sendResult = await sendDiscordMessage(recipient, message, config);
                break;
            case 'teams':
                sendResult = await sendTeamsMessage(recipient, message, subject, config);
                break;
            case 'slack':
                sendResult = await sendSlackMessage(recipient, message, config);
                break;
            case 'email':
                sendResult = await sendEmailMessage(recipient, message, subject, config);
                break;
            case 'sms':
                sendResult = await sendSMSMessage(recipient, message, config);
                break;
            default:
                throw new Error(`Unsupported notification channel: ${channel}`);
        }

        const sendTime = Date.now() - startTime;

        // Update notification status in database
        if (notificationId) {
            await updateNotificationStatus(notificationId, 'sent', null, sendTime);
        }

        return new Response(JSON.stringify({
            data: {
                channel,
                recipient,
                status: 'sent',
                send_time_ms: sendTime,
                result: sendResult
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Notification error:', error);

        // Update notification status with error
        const { notificationId } = await req.json().catch(() => ({}));
        if (notificationId) {
            await updateNotificationStatus(notificationId, 'failed', error.message);
        }

        const errorResponse = {
            error: {
                code: 'NOTIFICATION_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function sendTelegramMessage(chatId, message, config) {
    const { botToken } = config;
    
    if (!botToken || botToken === 'demo') {
        // Demo mode - don't actually send
        return {
            ok: true,
            result: {
                message_id: Math.floor(Math.random() * 100000),
                demo: true
            }
        };
    }

    const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
    
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            chat_id: chatId,
            text: message,
            parse_mode: 'HTML'
        })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Telegram API error: ${errorData.description || response.status}`);
    }

    return await response.json();
}

async function sendDiscordMessage(webhookUrl, message, config) {
    if (!webhookUrl || webhookUrl.includes('demo')) {
        // Demo mode
        return {
            id: 'demo_message_' + Math.floor(Math.random() * 100000),
            demo: true
        };
    }

    const payload = {
        content: message,
        username: config?.username || 'Enterprise Bot',
        avatar_url: config?.avatarUrl
    };

    const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Discord webhook error: ${response.status} - ${errorText}`);
    }

    return { status: 'sent', discord_response: response.status };
}

async function sendTeamsMessage(webhookUrl, message, subject, config) {
    if (!webhookUrl || webhookUrl.includes('demo')) {
        // Demo mode
        return {
            id: 'demo_teams_' + Math.floor(Math.random() * 100000),
            demo: true
        };
    }

    const payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": subject || "Notification",
        "sections": [{
            "activityTitle": subject || "Enterprise Automation",
            "activitySubtitle": new Date().toLocaleString(),
            "text": message,
            "markdown": true
        }]
    };

    const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Teams webhook error: ${response.status} - ${errorText}`);
    }

    return { status: 'sent', teams_response: response.status };
}

async function sendSlackMessage(webhookUrl, message, config) {
    if (!webhookUrl || webhookUrl.includes('demo')) {
        // Demo mode
        return {
            ok: true,
            demo: true
        };
    }

    const payload = {
        text: message,
        username: config?.username || 'Enterprise Bot',
        icon_emoji: config?.iconEmoji || ':robot_face:'
    };

    const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Slack webhook error: ${response.status} - ${errorText}`);
    }

    return await response.json();
}

async function sendEmailMessage(recipient, message, subject, config) {
    // For demo purposes, we'll simulate email sending
    // In production, this would integrate with SendGrid, AWS SES, etc.
    
    if (!config?.apiKey || config.apiKey === 'demo') {
        return {
            id: 'demo_email_' + Math.floor(Math.random() * 100000),
            to: recipient,
            subject: subject || 'Notification',
            demo: true
        };
    }

    // Example implementation for SendGrid
    const { apiKey, fromEmail } = config;
    
    const payload = {
        personalizations: [{
            to: [{ email: recipient }],
            subject: subject || 'Notification'
        }],
        from: { email: fromEmail || 'noreply@example.com' },
        content: [{
            type: 'text/plain',
            value: message
        }]
    };

    const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Email API error: ${response.status} - ${errorText}`);
    }

    return { status: 'sent', email_response: response.status };
}

async function sendSMSMessage(recipient, message, config) {
    // Demo SMS implementation
    if (!config?.apiKey || config.apiKey === 'demo') {
        return {
            sid: 'demo_sms_' + Math.floor(Math.random() * 100000),
            to: recipient,
            demo: true
        };
    }

    // Example implementation for Twilio
    const { accountSid, authToken, fromNumber } = config;
    
    const auth = btoa(`${accountSid}:${authToken}`);
    
    const formData = new URLSearchParams();
    formData.append('To', recipient);
    formData.append('From', fromNumber);
    formData.append('Body', message);

    const response = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Messages.json`, {
        method: 'POST',
        headers: {
            'Authorization': `Basic ${auth}`,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`SMS API error: ${errorData.message || response.status}`);
    }

    return await response.json();
}

async function updateNotificationStatus(notificationId, status, errorMessage = null, sendTime = null) {
    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        const updateData = {
            status,
            error_message: errorMessage
        };

        if (status === 'sent') {
            updateData.sent_at = new Date().toISOString();
        } else if (status === 'failed') {
            updateData.failed_at = new Date().toISOString();
            updateData.retry_count = 'retry_count + 1';
        }

        await fetch(`${supabaseUrl}/rest/v1/notifications?id=eq.${notificationId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
    } catch (error) {
        console.error('Failed to update notification status:', error);
    }
}