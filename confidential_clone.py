from git import Repo, Actor,GitCommandError
import shutil
import os
import argparse
from tqdm import tqdm


parser = argparse.ArgumentParser(description="Clone a git repo with anonymized data, to keep your beautiful green boxes.")

parser.add_argument("-s", "--source", dest="source", required=True, help="Path to the source repository.")
parser.add_argument("-d", "--dest", dest="dest", required=True, help="Path to the destination repository.")
parser.add_argument("-n", "--author-name", dest="author_name", required=True, help="Author name to be preserved.")
parser.add_argument("-e", "--author-email", dest="author_email", required=True, help="Author email to be preserved.")
parser.add_argument("-rn", "--replace-name", dest="replace_name", default=None, help="Replacement for other author name.")
parser.add_argument("-re", "--replace-email", dest="replace_email", default=None, help="Replacement for other author email.")
parser.add_argument("-en", "--expunged-name", dest="expunged_name", default="Expunged", help="The name set to everyone else in the repo.")
parser.add_argument("-ee", "--expunged-email", dest="expunged_email", default="expunged@email.com", help="The email set to everyone else in the repo.")
parser.add_argument("-ec", "--expunged-commit", dest="expunged_commit", default="[commit message removed for confidentiality]", help="The message set for every commit.")
parser.add_argument("-eb", "--expunged-branch", dest="expunged_branch", default="expunged-branch-", help="The branch name, which will end with its index number.")
parser.add_argument("-et", "--expunged-tag", dest="expunged_tag", default="expunged-tag-", help="The tag name, which will end with its index number.")
parser.add_argument("--merge-all", dest="merge_all", action='store_true', help="If set, all branches will be merged into the main branch.")




args = parser.parse_args()

source_repo_path = args.source
dest_repo_path = args.dest
author_name = args.author_name
author_email = args.author_email
replace_name = args.replace_name or args.author_name
replace_email = args.replace_email or args.author_email
expunged_name = args.expunged_name
expunged_email = args.expunged_email
expunged_commit = args.expunged_commit
expunged_branch = args.expunged_branch
expunged_tag = args.expunged_tag


# Make sure destination repo path is clean
if os.path.exists(dest_repo_path):
    shutil.rmtree(dest_repo_path)

# Create a new repository
dest_repo = Repo.init(dest_repo_path)
readme_file = "README.md"
with open(os.path.join(dest_repo_path, readme_file), 'a'):
    os.utime(os.path.join(dest_repo_path, readme_file), None)

author = Actor(replace_name, replace_email)
dest_repo.index.add([readme_file])
dest_repo.index.commit('Initial commit', author=author, committer=author)
# Set config details
with dest_repo.config_writer() as git_config:
    git_config.set_value('user', 'name', replace_name)
    git_config.set_value('user', 'email', replace_email)
# Open the source repository
source_repo = Repo(source_repo_path)

# Rename the default branch to 'main'
dest_repo.git.branch('-M', 'main')

main_branch_name = 'main'
main_branch = dest_repo.create_head(main_branch_name)
# This dictionary will map each commit in the source repo to its replicated commit in the destination repo
commit_map = {}


def expunge_name(name):
    return replace_name if name == author_name else expunged_name

def expunge_email(email):
    return replace_email if email == author_email else expunge_email


total_commits = sum(1 for _ in source_repo.iter_commits())
author_commits = 0
processed_commits = 0

print('Grabbing all commits...')

pbar = tqdm(total=total_commits, desc="Processing commits", unit="commit", bar_format="{desc}: {n_fmt}/{total_fmt} |{bar}|")
# First, replicate each commit from each branch
for branch in source_repo.branches:
    for commit in reversed(list(source_repo.iter_commits(branch))):
        if commit in commit_map:
            # Skip commit if it has already been copied
            continue

        with open(os.path.join(dest_repo_path, "dummy.txt"), "w") as file:
            file.write(commit.hexsha)

        # Add the file to the repository
        dest_repo.index.add(["dummy.txt"])

        # Find this commit's parents in the destination repo
        parents = [commit_map[parent] for parent in commit.parents if parent in commit_map]

        # Commit the change with the same author, committer, and time as the original commit
        author = Actor(expunge_name(commit.author.name), expunge_email(commit.author.email))
        committer = Actor(expunge_name(commit.committer.name), expunge_email(commit.committer.email))

        new_commit = dest_repo.index.commit(expunged_commit, author=author, committer=committer, author_date=commit.authored_datetime, commit_date=commit.committed_datetime, parent_commits=parents)

        # Add this commit to the map
        commit_map[commit] = new_commit

        #update tqdm
        processed_commits += 1
        pbar.update(1)
        if commit.author.name == author_name:
            author_commits += 1


pbar.close()


print(f"\nTotal commits processed: {processed_commits}")
print(f"Number of times the author {author_name} was found: {author_commits}")


print('Writing to new repo...')
branches = list(source_repo.branches)
pbar_branch = tqdm(total=len(branches), desc="Processing branches", unit="branch", bar_format="{desc}: {n_fmt}/{total_fmt} |{bar}|")
for index, branch in enumerate(branches):
    # Anonymize branch names
    dest_repo.create_head(f"{expunged_branch}{index}", commit_map[branch.commit])
    pbar_branch.update(1)
pbar_branch.close()

# Anonymize tags
if(len(source_repo.tags)):
    tags = list(source_repo.tags)
    pbar_tag = tqdm(total=len(tags), desc="Processing tags", unit="tag", bar_format="{desc}: {n_fmt}/{total_fmt} |{bar}|")
    for index, tag in enumerate(tags):
        # Anonymize tag names
        dest_repo.create_tag(f"{expunged_tag}{index}", ref=commit_map[tag.commit])
        pbar_tag.update(1)
    pbar_tag.close()


for remote in list(dest_repo.remotes):
    dest_repo.delete_remote(remote)


# Merge all branches into the main branch and delete them afterwards if merge_all is set to True
if args.merge_all:
    print('Merging all and deleting.')
    branches_to_merge = [branch for branch in dest_repo.branches if branch != main_branch]
    for branch in tqdm(branches_to_merge, desc='Merging and deleting branches', unit='branch',bar_format="{desc}: {n_fmt}/{total_fmt} |{bar}|"):
        dest_repo.git.checkout(main_branch_name)
        try:
            dest_repo.git.merge(branch, strategy_option='theirs')
        except GitCommandError:
            print(f"Failed to merge {branch}. Resolving conflicts by favoring 'theirs'.")
            dest_repo.git.checkout('--', '.')
            dest_repo.git.commit('-m', f"Merge {branch} resolving conflicts by favoring 'theirs'.")
        dest_repo.delete_head(branch, '-D')


print('Done.')