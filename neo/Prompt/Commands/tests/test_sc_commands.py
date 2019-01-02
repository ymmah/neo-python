import os
import shutil
import json
import warnings
from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.SC import CommandSC
from neo.Prompt.PromptData import PromptData
from mock import patch
from io import StringIO


class CommandSCTestCase(WalletFixtureTestCase):
    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet1 = None

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            shutil.copyfile(cls.wallet_1_path(), cls.wallet_1_dest())
            cls._wallet1 = UserWallet.Open(CommandSCTestCase.wallet_1_dest(),
                                           to_aes_key(CommandSCTestCase.wallet_1_pass()))
        return cls._wallet1

    @classmethod
    def tearDown(cls):
        PromptData.Wallet = None
        try:
            os.remove("neo/Prompt/Commands/tests/SampleSC.avm")
            os.remove("neo/Prompt/Commands/tests/SampleSC.debug.json")
        except FileNotFoundError:  # expected during test_sc
            pass

    def test_sc(self):
        # with no subcommand
        with patch('sys.stdout', new=StringIO()) as mock_print:
            res = CommandSC().execute(None)
            self.assertFalse(res)
            self.assertIn("run `sc help` to see supported queries", mock_print.getvalue())

        # with invalid command
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['badcommand']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("badcommand is an invalid parameter", mock_print.getvalue())

    def test_sc_build(self):
        warnings.filterwarnings('ignore', category=ResourceWarning)  # filters warnings about unclosed files
        # test no input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameter", mock_print.getvalue())

        # test bad path
        args = ['build', 'SampleSC.py']
        res = CommandSC().execute(args)
        self.assertFalse(res)

        # test successful compilation
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build', 'neo/Prompt/Commands/tests/SampleSC.py']
            res = CommandSC().execute(args)
            self.assertTrue(res)
            self.assertIn("Saved output to neo/Prompt/Commands/tests/SampleSC.avm", mock_print.getvalue())

    def test_sc_buildrun(self):
        warnings.filterwarnings('ignore', category=ResourceWarning)  # filters warnings about unclosed files
        # test no input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameters", mock_print.getvalue())

        # test bad path
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'SampleSC.py', 'True', 'False', 'False', '070502', '02', '--i']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertEqual(tx, None)
            self.assertEqual(result, None)
            self.assertEqual(total_ops, None)
            self.assertEqual(engine, None)
            self.assertIn("Please check the path to your Python (.py) file to compile", mock_print.getvalue())

        # test no open wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '070502', '02', 'add' 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy' '3']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertEqual(tx, None)
            self.assertEqual(result, None)
            self.assertEqual(total_ops, None)
            self.assertEqual(engine, None)
            self.assertIn("Please open a wallet to test build contract", mock_print.getvalue())

        # test bad args
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', '070502', '02', 'add', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '3']  # missing payable flag
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("run `sc build_run help` to see supported queries", mock_print.getvalue())

        # test successful build and run
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '070502', '02', 'add', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '3']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertTrue(tx)
            self.assertEqual(str(result[0]), '3')
            self.assertIn("Test deploy invoke successful", mock_print.getvalue())

        # test successful build and run with prompted input
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('prompt_toolkit.shortcuts.PromptSession.prompt', side_effect=['remove', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '3']):
                args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '070502', '02', '--i']
                tx, result, total_ops, engine = CommandSC().execute(args)
                self.assertTrue(tx)
                self.assertEqual(str(result[0]), '0')
                self.assertIn("Test deploy invoke successful", mock_print.getvalue())

        # test invoke failure (SampleSC requires three inputs)
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '0705', '02', 'balance', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertIsNone(tx)
            self.assertIn("Test invoke failed", mock_print.getvalue())

    def test_sc_loadrun(self):
        warnings.filterwarnings('ignore', category=ResourceWarning)  # filters warnings about unclosed files
        # test no input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameters", mock_print.getvalue())

        # test bad path
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '070502', '02', '--i']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("run `sc load_run help` to see supported queries", mock_print.getvalue())

        # build the .avm file
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build', 'neo/Prompt/Commands/tests/SampleSC.py']
            res = CommandSC().execute(args)
            self.assertTrue(res)
            self.assertIn("Saved output to neo/Prompt/Commands/tests/SampleSC.avm", mock_print.getvalue())

        # test no open wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run', 'neo/Prompt/Commands/tests/SampleSC.avm', 'True', 'False', 'False', '070502', '02', 'add' 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy' '3']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertEqual(tx, None)
            self.assertEqual(result, None)
            self.assertEqual(total_ops, None)
            self.assertEqual(engine, None)
            self.assertIn("Please open a wallet to test build contract", mock_print.getvalue())

        # test bad args
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run', 'neo/Prompt/Commands/tests/SampleSC.avm', 'True', 'False', '070502', '02', 'balance', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '0']  # missing payable flag
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("run `sc load_run help` to see supported queries", mock_print.getvalue())

        # test successful load and run with from-addr
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run', 'neo/Prompt/Commands/tests/SampleSC.avm', 'True', 'False', 'False', '070502', '02', 'balance', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '0', '--from-addr=' + self.wallet_1_addr]
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertTrue(tx)
            self.assertIn("Test deploy invoke successful", mock_print.getvalue())