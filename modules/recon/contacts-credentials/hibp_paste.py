from recon.core.module import BaseModule
import urllib

class Module(BaseModule):

    meta = {
        'name': 'Have I been pwned? Paste Search',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages the haveibeenpwned.com API to determine if email addresses have been published to various paste sites. Adds compromised email addresses to the \'credentials\' table.',
        'comments': (
            'Paste sites supported: Pastebin, Pastie, or Slexy',
        ),
        'query': 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email',
        'options': (
            ('download', True, True, 'download pastes'),
        ),
    }

    def module_run(self, accounts):
        sites = {
            'Pastebin': 'http://pastebin.com/raw.php?i=%s',
            'Pastie': 'http://pastie.org/pastes/%s/text',
            'Slexy': 'http://slexy.org/raw/%s',
            }
        # retrieve status
        base_url = 'https://haveibeenpwned.com/api/v2/%s/%s'
        endpoint = 'pasteaccount'
        for account in accounts:
            resp = self.request(base_url % (endpoint, urllib.quote(account)))
            rcode = resp.status_code
            if rcode == 404:
                self.verbose('%s => Not Found.' % (account))
            elif rcode == 400:
                self.error('%s => Bad Request.' % (account))
                continue
            else:
                for paste in resp.json:
                    fileurl = sites[paste['Source']] % (paste['Id'])
                    self.alert('%s => Paste found! Seen in a %s on %s (%s).' % (account, paste['Source'], paste['Date'], fileurl))
                    if self.options['download'] == True:
                        resp = self.request(fileurl)
                        if resp.status_code == 200:
                            filepath = '%s/%s_%s_%s.txt' % (self.workspace, account, paste['Source'], paste['Id'])
                            dl = open(filepath, 'w')
                            dl.write(resp.text.encode(resp.encoding) if resp.encoding else resp.text)
                            dl.close()
                            self.verbose('Paste stored at \'%s\'.' % (filepath))
                        else:
                            self.output('Paste could not be downloaded (%s).' % (fileurl))
                self.add_credentials(account)
