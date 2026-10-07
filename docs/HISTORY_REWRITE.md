# History rewrite before publication

On 7 October 2026, before the first push, the local repository history (51 commits on main) was rewritten under the owner's decisions of 6 and 7 October 2026. The purpose was public release without a personal email address or local workspace paths.

Changes applied throughout the history:

- Author and committer email addresses were replaced with 241006549+oakridge-i@users.noreply.github.com. Author names, dates, messages and commit order were retained.
- The absolute workspace prefix inside the Windows user profile was replaced with `<workspace>` in DECISIONS.md, docs/MASTER_PLAN.md, docs/n0/AAPL_REUSE_AUDIT.md and the two historical N0 setup documents, docs/n0/NEW_CHAT_BRIEF.md and docs/n0/NEW_PROJECT_SETUP.md. These filenames identify the historical rewrite scope; the setup documents are excluded from the current public documentation edition.
- One line in experiments/EXPERIMENT_LOG.jsonl was changed: the failed record for run 20261006T103621-754f18207b contained the same path in its JSON-escaped SSL error. The path was replaced with the same marker; all other fields and lines were retained. The owner approved this exception to log immutability on 7 October 2026.

There were no other content changes in that rewrite. Each old/new commit pair was checked for differences limited to lines containing the path. The test suite after the rewrite reported 149 passed. The complete original history is preserved in a local Git bundle (SHA-256 e4e1c595b4e7f5bdf7faf10b9f1965e23518a9389d5f375128efc6ead11f2d1d), which is not published.

The log's git_sha fields, STATUS.md, DECISIONS.md, N1 reports and reviews retain the original commit hashes. The mapping below follows historical order. Full commit hashes identify each historical revision; the mapping does not depend on commit-message wording. The subsequent English editorial edition is described in [DOCUMENTATION_EDITION.md](DOCUMENTATION_EDITION.md).

| Original commit | Rewritten commit |
| --- | --- |
| 1f32ac1a9e8d2d71c26ed6579faf80786dca9aea | e483bad72f1933b6c57312f758585d78bcd0ac2b |
| 18d56f84e624f84add89f28be66954fea23891f4 | 50f7757e32dd5381adefad0988827bd469eecf06 |
| 7815266f890383f157b9e407a8e2b61173c62f7e | f97cbda4318be23ca63dfd6bfb1fd869dd3c0faa |
| e7935122a2c2ee8abefd29082ea7c0a0565630a4 | 567215f760ca2fff7765705ffd8b12c499b31f78 |
| 16436512c6df7ea2a58b0c2eb64ea0abebc5590f | f757d4a3e8afa39bd61229eab7ca5912e11b648d |
| 80f75c9800284aa856d137b09255ef074b31b528 | 88d1121c6d94138a07fa5b0ee46d80a38f8ce69f |
| ff424213fd878a4fd026781cd8ed27d5792a629f | 8f981c25b871b5a7511bc059279a49af6f985f2f |
| 9d23ee1be04f344f0d079cb1ad75384b6b1778d4 | 267d784daeb60cf1349cc79b09656e4ca4478784 |
| b45ed114d70ef8263806babc0576e057440112eb | 2b01c012150bc6582ae903199a5a511a322da70b |
| 62e1ab730f1e2138d17c848942dd93ac8107b494 | e3a25ae755d4a5280c165ba2ce90a689ab124a29 |
| 5130ec2b1392e3ccace22c24f0f687d029a56880 | 9f2824340440ad539ed326774aaa7b49ea8fbb14 |
| caf0a12a1d8e05cd98900cc9f3e1b6bb41faddde | 8a90c512a2a7cc164d11b686a5b56764bc32cd4e |
| a03983dffff0dae5347d3ffb9a19371c36d8d87c | 526cf2a03a4125572ade4431f805c4aab629f45e |
| 590281ea6f2fc4b24e75ab83d6c63602ed018de0 | 38274ccd97fcc17b836be6407110b47432d9bb82 |
| c78a319f6bbf2020aab7cf06f4d671a3fed7e387 | 9e07a70d9e1e04b4817cde5ff877f3a9626d6d3c |
| 8e677d16326fee3066c4f89f9e6fb7e70113452b | 48affd5d07b5c18cd6e31b282aa2d911f6b03379 |
| cdaaf85d3e33f0b3fb032893931dce8f21eebd0d | eecf56e1e7f68253464e58ae38a221963807b080 |
| fa8fe34d779fe47b9bcb5957c16f096a8b9f5cb1 | 6c2e9b38449b058af184a282c0df3540defd30a9 |
| e0e312ac55e7d9054f1f17e3241619b70105c19f | c1cffddd791007e8e8f2a8565e9d0be85c3f7eab |
| 0a892be1975f7bb4052b1bebc01ad1a1816ec87e | 469e9bfe17c10dd18fd7d7fa772f95dc29fd05d8 |
| 12ca5dc81ca3e54ab9e82b025ac50cac159c41c0 | d549bc7e898771add08e8c700cb129be10f0cd31 |
| 977eaf66c12815b8de86c7d61c36c223f7673caa | aecfd1cff63ca7ea27ac196dd2e6b992d99f665e |
| 9c48906d13f9d80740707d96b181b1c6c0f18a00 | c5586a6bdedd270c61b361bd44e5dfd000c09ea5 |
| 799eef9de45825c5e63c9de39d72a8b4bf15a7e9 | a07cad7f8ec977ebaa073137b0a8cf2c927a2941 |
| 53ab5acc36241ded5e64de6e463e8dda40cd0d16 | 772445252f8014d2cc507b454bae057c2c0bcb7d |
| a51a53194d063693f37b3d58570a932c6681492f | 40f56c209748c83db91a24ac1eca4b376b978686 |
| 0cf86791a06a7de14f2964091d0bfc9954ab55b1 | 21243bba3b67492f7ea66915a9d9e4af9b53f93e |
| 72d862e2bfd52208d90e608a1b30e2c3126aa969 | c064a203ee53029eec8ffa24106b7be7975b4ec3 |
| e4d166944106b41a17830b606fb5b5e6d3096e12 | 668980417b8e345a3580dd1ee95b0ebcc768d0cf |
| 13bc5766b9c62dd7ea0b09b63c8ca051fb6b8e4a | 38a0c2a17b746a4328d2c449538591801898ee0b |
| 8f9e0b46db9d4ec3a83351452b8fbc276c301c86 | 4a259d8cd2abd940f014d389c9e4149d3eba1db0 |
| 86b0715ad49a9dbee2574684a52a8ebfd13b0e89 | ef6a235a244faf0288d6131fb1d0302d751ec560 |
| 54169388278062c31674832cc8ca61b7dc160d18 | 37cd491764271b2a5c577b459cc953331d065b5e |
| 56fdf278bfef58cb90485513e42d12445792b26c | 865e614450c50d2ef217f5ab6e6c2d89f47d464c |
| c41e57e6b6b1f9d0cba7ab0769b1a8e33a92bd63 | 2b957e3c141580f215044b2a40f0c848ac89402f |
| d27af5db8c632af6ec940f2b6214864f727a497b | 567ddb3e875dacfcf18c50b75c0382de20e4455a |
| 88e6adbc3740c87d1d119436b4e5e394961019bd | 0fa4d16500043afd55c1b1e1d4cb1b5a7da921e7 |
| 7a0c67711332bd119cc54c8c21e7ae7e144d5bbe | d6180140922915cb3d6b5adaf0339b8728bdb758 |
| f091aa2ad31ab96726861727f283d7509670a827 | 719919d431c85d86a11beede2a3786db34b897a2 |
| 02af65edaabe594262c887cad5a4492e6b17264e | 5bbdf50ee2a6f74cacbd6275837ae9d63f01ee0a |
| ba21e58fb75fa9d77a6feaa72a7abe49cf5bf92f | a7dc5b8845c0a884e901539b69c727ef6af79d2a |
| 0a0e865919325dd1b79a1ee7efa375e7c08e4dbb | 7398f33769ded55ef2717be6ca11bd406fe75ff0 |
| ae2cd38501ab23ce2b4afb284d2abb5ef6632fb4 | 54d56e46979fa9b4f085dd486270bacd71b95fcf |
| 6e33721d88a5e0bbf6714580d87e74c9ee374270 | 774e315a3af4bc71235e0cda13f4344874175d6c |
| a2019d79b20511e156d8728b9af2c9a935f66425 | 48e1db8cc4fdc500870d5b284b001a20d0ce5944 |
| 02668962bc21ddcc73f39c7aaa2b37a0cce25ea4 | f3e3537575e7d623f777dfa62412a769228babb7 |
| 5a8eac5dc10ef3fe493c1198db2dc75c2bd32161 | 2529fba58886e1964bc01f470e9a2db1ca8611a4 |
| d936e91f4dab074e67182f8967264d89d13b1a02 | d00abd25725fdafa4c4028903959a04dade37a46 |
| 591352a6e16bb39cb8ea6f5f5338056b5f539af4 | f6cdb0de8e56531630d90f6c4e55566763a33378 |
| 1ec936330cce0a6d5a4e009110ae603c4ed7cf8f | c1b86d490ac52372e9ca098122f71f5fe9cad507 |
| ce84282c1a96237eaeb3302612498570747179a5 | f3686dae6104c97658f66ce1fe712a5aa03c11d4 |
