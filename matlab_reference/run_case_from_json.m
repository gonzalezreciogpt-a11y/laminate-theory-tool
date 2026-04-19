function run_case_from_json(input_json_path, output_json_path)
% RUN_CASE_FROM_JSON
% Reads a JSON manifest, executes the legacy-compatible MATLAB wrapper and
% writes structured JSON outputs.

raw = fileread(input_json_path);
case_data = jsondecode(raw);
result = legacy_reference_runner(case_data);

json_text = jsonencode(result);
fid = fopen(output_json_path, 'w');
if fid == -1
    error("Could not open output file '%s' for writing.", output_json_path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, '%s\n', json_text);
end
