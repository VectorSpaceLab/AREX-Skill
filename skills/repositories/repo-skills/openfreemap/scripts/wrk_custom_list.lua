-- Replay OpenFreeMap tile paths with wrk.
--
-- Configuration through environment variables:
--   OFM_PATH_LIST   path to a newline-delimited list of replay paths
--   OFM_URL_BASE    leading path prefix, defaults to /planet/fake_version/
--   OFM_HOST_HEADER Host header to send with requests, defaults to ofm
--
-- Example:
--   OFM_PATH_LIST=path_list_500k.txt wrk -c10 -t4 -d60s -s scripts/wrk_custom_list.lua http://localhost

local counter = 1
local lines = {}
local url_base = os.getenv("OFM_URL_BASE") or "/planet/fake_version/" -- trailing slash
local path_list_txt = os.getenv("OFM_PATH_LIST") or "path_list_500k.txt"
local host_header = os.getenv("OFM_HOST_HEADER") or "ofm"

for line in io.lines(path_list_txt) do
    if line ~= "" then
        table.insert(lines, url_base .. line)
    end
end

if #lines == 0 then
    error("empty replay list: " .. path_list_txt)
end

local function getNextUrl()
    local url_path = lines[counter]
    counter = counter + 1

    if counter > #lines then
        counter = 1
    end

    return url_path
end

request = function()
    path = getNextUrl()
    local headers = {}
    headers["Host"] = host_header
    return wrk.format('GET', path, headers, nil)
end

response = function(status)
    if status ~= 200 then
        print("Non-200 response")
        print("Status:", status)
        print("Request path:", path)
    end
end
