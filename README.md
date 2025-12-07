# AWS-Recon
Automation to enumerate AWS key / secret details

```bash
$ ./aws_recon.sh AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

## Example usage
![](./notebook_snippets_43.JPG)

## Helper Tools

### rg pattern
Not the best of all worlds, but works.

```bash
$ rg -azioIN "((?i:AWS_ACCESS_KEY_ID)\s?=\s?[\"']?[A-Z0-9]{20}[\"']?)|((?i:AWS_ACCESS_KEY)\s?=\s?[\"']?[A-Z0-9]{20}[\"']?)|((?i:AWS_KEY_ID)\s?=\s?[\"']?[A-Z0-9]{20}[\"']?)|((?i:AWS_KEY)\s?=\s?[\"']?[A-Z0-9]{20}[\"']?)|((?i:AWS_SECRET_ACCESS_KEY)\s?=\s?[\"']?[A-Za-z0-9/+=]{40}[\"']?)|((?i:AWS_SECRET_KEY)\s?=\s?[\"']?[A-Za-z0-9/+=]{40}[\"']?)|((?i:AWS_ACCESS_SECRET)\s?=\s?[\"']?[A-Za-z0-9/+=]{40}[\"']?)|((?i:AWS_SECRET)\s?=\s?[\"']?[A-Za-z0-9/+=]{40}[\"']?)" 2>/dev/null | tee AWS_grep_results.txt 
```

### Grep Output Cleaner
- Tries to find matching key - secret pairs
- Sorts out trash
- Unifies Key naming to "AWS_ACCESS_KEY_ID" - "AWS_SECRET_ACCESS_KEY"
- Optional `-l` oneliner output <key> <secret> to use in a loop with awsRecon.sh
  
```bash
$ aws_keylist_cleaner.py -l AWS_grep_results.txt cleaned_AWS_grep_results.txt
```

```bash
$ cat cleaned_AWS_grep_results.txt | while read -r line; do echo $line; awsRecon.sh "${line%% *}" "${line##* }"; done
```
