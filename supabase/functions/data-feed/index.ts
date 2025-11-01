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
        const { source, config, feedId } = requestData;

        if (!source || !config) {
            throw new Error('Source and config are required parameters');
        }

        let apiResponse;
        const startTime = Date.now();

        // Fetch data based on source type
        switch (source) {
            case 'github':
                apiResponse = await fetchGitHubData(config);
                break;
            case 'alpha_vantage':
                apiResponse = await fetchAlphaVantageData(config);
                break;
            case 'weather_api':
                apiResponse = await fetchWeatherData(config);
                break;
            case 'news_api':
                apiResponse = await fetchNewsData(config);
                break;
            case 'guardian_api':
                apiResponse = await fetchGuardianData(config);
                break;
            default:
                throw new Error(`Unsupported data source: ${source}`);
        }

        const responseTime = Date.now() - startTime;

        // Save to database if feedId provided
        if (feedId) {
            await saveFeedData(feedId, apiResponse, responseTime, 'success');
            await updateFeedStatus(feedId, apiResponse);
        }

        return new Response(JSON.stringify({
            data: {
                source,
                timestamp: new Date().toISOString(),
                response_time_ms: responseTime,
                data: apiResponse
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Data feed error:', error);

        // Save error to database if feedId provided
        const { feedId } = await req.json().catch(() => ({}));
        if (feedId) {
            await saveFeedData(feedId, null, Date.now() - Date.now(), 'error', error.message);
        }

        const errorResponse = {
            error: {
                code: 'DATA_FEED_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function fetchGitHubData(config) {
    const { endpoint, owner, repo } = config;
    
    let url;
    switch (endpoint) {
        case 'repos':
            url = `https://api.github.com/repos/${owner}/${repo}`;
            break;
        case 'commits':
            url = `https://api.github.com/repos/${owner}/${repo}/commits?per_page=10`;
            break;
        case 'issues':
            url = `https://api.github.com/repos/${owner}/${repo}/issues?state=open&per_page=10`;
            break;
        case 'releases':
            url = `https://api.github.com/repos/${owner}/${repo}/releases/latest`;
            break;
        default:
            throw new Error(`Unsupported GitHub endpoint: ${endpoint}`);
    }

    const response = await fetch(url, {
        headers: {
            'User-Agent': 'Supabase-Edge-Function',
            'Accept': 'application/vnd.github.v3+json'
        }
    });

    if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status}`);
    }

    return await response.json();
}

async function fetchAlphaVantageData(config) {
    const { function: func, symbol, interval, apikey } = config;
    
    if (!apikey || apikey === 'demo') {
        // Use demo key for testing
        const url = `https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Alpha Vantage API error: ${response.status}`);
        }
        
        return await response.json();
    }

    const url = `https://www.alphavantage.co/query?function=${func}&symbol=${symbol}&interval=${interval}&apikey=${apikey}`;
    
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Alpha Vantage API error: ${response.status}`);
    }

    return await response.json();
}

async function fetchWeatherData(config) {
    const { city, appid } = config;
    
    if (!appid || appid === 'demo') {
        // Return demo weather data
        return {
            weather: [{ main: 'Clear', description: 'clear sky' }],
            main: { temp: 22.5, humidity: 60 },
            name: city || 'Demo City',
            dt: Math.floor(Date.now() / 1000)
        };
    }

    const url = `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${appid}&units=metric`;
    
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Weather API error: ${response.status}`);
    }

    return await response.json();
}

async function fetchNewsData(config) {
    const { q, category, country, apiKey } = config;
    
    if (!apiKey || apiKey === 'demo') {
        // Return demo news data
        return {
            articles: [
                {
                    title: 'Demo News Article',
                    description: 'This is a demonstration news article for testing purposes.',
                    url: 'https://example.com/demo-article',
                    publishedAt: new Date().toISOString(),
                    source: { name: 'Demo News' }
                }
            ],
            totalResults: 1
        };
    }

    let url = 'https://newsapi.org/v2/top-headlines?';
    
    if (q) url += `q=${encodeURIComponent(q)}&`;
    if (category) url += `category=${category}&`;
    if (country) url += `country=${country}&`;
    
    url += `apiKey=${apiKey}`;

    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`News API error: ${response.status}`);
    }

    return await response.json();
}

async function fetchGuardianData(config) {
    const { q, section, apiKey } = config;
    
    if (!apiKey || apiKey === 'demo') {
        // Return demo Guardian data
        return {
            response: {
                results: [
                    {
                        webTitle: 'Demo Guardian Article',
                        webUrl: 'https://example.com/demo-guardian',
                        webPublicationDate: new Date().toISOString(),
                        sectionName: section || 'Demo Section'
                    }
                ]
            }
        };
    }

    let url = `https://content.guardianapis.com/search?api-key=${apiKey}`;
    
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (section) url += `&section=${section}`;

    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Guardian API error: ${response.status}`);
    }

    return await response.json();
}

async function saveFeedData(feedId, data, responseTime, status, errorMessage = null) {
    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        const insertData = {
            feed_id: feedId,
            data: data || {},
            response_time_ms: responseTime,
            status,
            error_message: errorMessage
        };

        await fetch(`${supabaseUrl}/rest/v1/data_feed_history`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(insertData)
        });
    } catch (error) {
        console.error('Failed to save feed data:', error);
    }
}

async function updateFeedStatus(feedId, data) {
    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        const updateData = {
            latest_data: data,
            last_fetch_at: new Date().toISOString(),
            error_count: 0,
            last_error: null
        };

        await fetch(`${supabaseUrl}/rest/v1/real_time_data_feeds?id=eq.${feedId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
    } catch (error) {
        console.error('Failed to update feed status:', error);
    }
}